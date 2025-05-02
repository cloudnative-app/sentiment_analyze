import os
import pandas as pd
from google.cloud import language_v1
import json
from google.api_core.client_options import ClientOptions
from dotenv import load_dotenv
from datetime import datetime
import requests
import re
import time
from requests.exceptions import RequestException
import logging
import sys

# 한글 인코딩 설정
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analysis.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Perspective API rate limiting constants
PERSPECTIVE_API_DELAY = 1.1  # 1.1초 딜레이 (초당 1개 요청 제한)
MAX_RETRIES = 3  # 최대 재시도 횟수
RETRY_DELAY = 5  # 재시도 간 딜레이 (초)

def extract_messages(message_text):
    """Extracts individual messages from the combined message text."""
    try:
        # Regular expression to match messages with line numbers
        pattern = r'(\d+:)?\s*"([^"]+)"'
        matches = re.findall(pattern, message_text)
        messages = [match[1].strip() for match in matches]
        if not messages:
            logging.warning(f"No messages found in text: {message_text}")
        return messages
    except Exception as e:
        logging.error(f"Error extracting messages: {str(e)}")
        return []

def analyze_perspective(text, api_key):
    """Analyzes text toxicity using Perspective API with rate limiting and retries."""
    PERSPECTIVE_API_URL = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
    
    url = f"{PERSPECTIVE_API_URL}?key={api_key}"
    
    data = {
        'comment': {'text': text},
        'languages': ['ko'],
        'requestedAttributes': {
            'TOXICITY': {},
            'SEVERE_TOXICITY': {},
            'IDENTITY_ATTACK': {},
            'INSULT': {},
            'PROFANITY': {},
            'THREAT': {}
        }
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            # API 요청 전 딜레이 추가
            time.sleep(PERSPECTIVE_API_DELAY)
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            results = response.json()
            
            # Extract scores from the response
            scores = {}
            for attr, score_data in results.get('attributeScores', {}).items():
                scores[attr] = score_data['summaryScore']['value']
            
            return scores
            
        except RequestException as e:
            if attempt < MAX_RETRIES - 1:
                logging.warning(f"Perspective API request failed (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
                logging.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Perspective API request failed after {MAX_RETRIES} attempts: {str(e)}")
                return None
        except Exception as e:
            logging.error(f"Unexpected error in Perspective API: {str(e)}")
            return None

def analyze_sentiment(text, api_key):
    """Analyzes sentiment using Google Cloud Natural Language API."""
    try:
        client_options = ClientOptions(api_key=api_key)
        client = language_v1.LanguageServiceClient(client_options=client_options)
        
        document = language_v1.Document(
            content=text,
            type_=language_v1.Document.Type.PLAIN_TEXT,
            language="ko"
        )
        
        # Analyze sentiment
        sentiment = client.analyze_sentiment(
            request={"document": document}
        ).document_sentiment
        
        return {
            "score": sentiment.score,
            "magnitude": sentiment.magnitude
        }
    except Exception as e:
        logging.error(f"Sentiment analysis error: {str(e)}")
        return None

def process_csv(input_file, api_key):
    """Process the CSV file and analyze messages."""
    try:
        # Read CSV file with explicit encoding
        df = pd.read_csv(input_file, encoding='utf-8')
        logging.info(f"Successfully read {len(df)} rows from {input_file}")
        
        # Determine message column name
        message_column = None
        possible_columns = ['근거 메시지 (라인 번호 또는 내용)', '대표 메시지 (근거)']
        for col in possible_columns:
            if col in df.columns:
                message_column = col
                break
        
        if not message_column:
            logging.error(f"Could not find message column in {input_file}")
            return None
        
        logging.info(f"Using message column: {message_column}")
        
        # Add new columns for analysis results
        df['Google 감정 점수'] = None
        df['Google 감정 강도'] = None
        df['Perspective 유해성'] = None
        df['Perspective 심각한 유해성'] = None
        df['Perspective 정체성 공격'] = None
        df['Perspective 모욕'] = None
        df['Perspective 욕설'] = None
        df['Perspective 위협'] = None
        
        # Process all rows
        for index, row in df.iterrows():
            try:
                message_text = row[message_column]
                if pd.isna(message_text):
                    logging.warning(f"Empty message in row {index + 1}")
                    continue
                    
                # Extract individual messages
                messages = extract_messages(message_text)
                if not messages:
                    continue
                
                # Process each individual message
                for msg_idx, message in enumerate(messages):
                    try:
                        # Analyze sentiment
                        sentiment_result = analyze_sentiment(message, api_key)
                        if sentiment_result:
                            df.at[index, 'Google 감정 점수'] = sentiment_result['score']
                            df.at[index, 'Google 감정 강도'] = sentiment_result['magnitude']
                        
                        # Analyze with Perspective API
                        perspective_result = analyze_perspective(message, api_key)
                        if perspective_result:
                            df.at[index, 'Perspective 유해성'] = perspective_result.get('TOXICITY')
                            df.at[index, 'Perspective 심각한 유해성'] = perspective_result.get('SEVERE_TOXICITY')
                            df.at[index, 'Perspective 정체성 공격'] = perspective_result.get('IDENTITY_ATTACK')
                            df.at[index, 'Perspective 모욕'] = perspective_result.get('INSULT')
                            df.at[index, 'Perspective 욕설'] = perspective_result.get('PROFANITY')
                            df.at[index, 'Perspective 위협'] = perspective_result.get('THREAT')
                        
                        logging.info(f"Processed row {index + 1}, message {msg_idx + 1}/{len(messages)} from {os.path.basename(input_file)}")
                        
                    except Exception as e:
                        logging.error(f"Error processing message {msg_idx + 1} in row {index + 1}: {str(e)}")
                        continue
                
            except Exception as e:
                logging.error(f"Error processing row {index + 1}: {str(e)}")
                continue
        
        return df
    except Exception as e:
        logging.error(f"Error processing file {input_file}: {str(e)}")
        return None

def main():
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key from environment variable
        api_key = os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            logging.error("GOOGLE_API_KEY not found in .env file")
            print("Error: GOOGLE_API_KEY not found in .env file")
            print("Please create a .env file with your Google Cloud API key")
            print("Example: GOOGLE_API_KEY=your-api-key-here")
            return
        
        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
        
        # Get all CSV files from input directory
        input_files = [os.path.join('input', f) for f in os.listdir('input') if f.endswith('.csv')]
        logging.info(f"Found {len(input_files)} CSV files to process")
        
        # Process all files
        for input_file in input_files:
            logging.info(f"\nProcessing file: {input_file}")
            results_df = process_csv(input_file, api_key)
            
            if results_df is not None:
                # Create timestamp for filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.basename(input_file)
                output_file = f'output/{os.path.splitext(filename)[0]}_analysis_{timestamp}.csv'
                
                # Save to output file with explicit encoding
                results_df.to_csv(output_file, encoding='utf-8-sig', index=False)
                logging.info(f"Results saved to {output_file}")
            else:
                logging.error(f"Failed to process file: {input_file}")
                
    except Exception as e:
        logging.error(f"Unexpected error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
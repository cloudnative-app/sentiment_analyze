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
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analysis.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

@dataclass
class AnalysisConfig:
    """Configuration for sentiment and toxicity analysis."""
    api_key: str
    perspective_api_delay: float = 1.1
    max_retries: int = 3
    retry_delay: int = 5
    message_columns: List[str] = None

    def __post_init__(self):
        if self.message_columns is None:
            self.message_columns = [
                'message', 'text', 'content', 'comment', 'review',
                '메시지', '내용', '댓글', '리뷰'
            ]

class SentimentAnalyzer:
    """A class for analyzing sentiment and toxicity in text using Google Cloud APIs."""
    
    def __init__(self, config: AnalysisConfig):
        """Initialize the analyzer with configuration."""
        self.config = config
        self.perspective_api_url = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
        
    def extract_messages(self, message_text: str) -> List[str]:
        """Extract individual messages from combined message text."""
        try:
            pattern = r'(\d+:)?\s*"([^"]+)"'
            matches = re.findall(pattern, message_text)
            messages = [match[1].strip() for match in matches]
            if not messages:
                logging.warning(f"No messages found in text: {message_text}")
            return messages
        except Exception as e:
            logging.error(f"Error extracting messages: {str(e)}")
            return []
    
    def analyze_perspective(self, text: str) -> Optional[Dict[str, float]]:
        """Analyze text toxicity using Perspective API."""
        url = f"{self.perspective_api_url}?key={self.config.api_key}"
        
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
        
        for attempt in range(self.config.max_retries):
            try:
                time.sleep(self.config.perspective_api_delay)
                response = requests.post(url, json=data)
                response.raise_for_status()
                
                results = response.json()
                scores = {}
                for attr, score_data in results.get('attributeScores', {}).items():
                    scores[attr] = score_data['summaryScore']['value']
                
                return scores
                
            except RequestException as e:
                if attempt < self.config.max_retries - 1:
                    logging.warning(f"Perspective API request failed (attempt {attempt + 1}/{self.config.max_retries}): {str(e)}")
                    logging.info(f"Retrying in {self.config.retry_delay} seconds...")
                    time.sleep(self.config.retry_delay)
                else:
                    logging.error(f"Perspective API request failed after {self.config.max_retries} attempts: {str(e)}")
                    return None
            except Exception as e:
                logging.error(f"Unexpected error in Perspective API: {str(e)}")
                return None
    
    def analyze_sentiment(self, text: str) -> Optional[Dict[str, float]]:
        """Analyze sentiment using Google Cloud Natural Language API."""
        try:
            client_options = ClientOptions(api_key=self.config.api_key)
            client = language_v1.LanguageServiceClient(client_options=client_options)
            
            document = language_v1.Document(
                content=text,
                type_=language_v1.Document.Type.PLAIN_TEXT,
                language="ko"
            )
            
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
    
    def process_dataframe(self, df: pd.DataFrame, message_column: str) -> pd.DataFrame:
        """Process a DataFrame containing messages."""
        # Add new columns for analysis results
        df['Google 감정 점수'] = None
        df['Google 감정 강도'] = None
        df['Perspective 유해성'] = None
        df['Perspective 심각한 유해성'] = None
        df['Perspective 정체성 공격'] = None
        df['Perspective 모욕'] = None
        df['Perspective 욕설'] = None
        df['Perspective 위협'] = None
        
        for index, row in df.iterrows():
            try:
                message_text = row[message_column]
                if pd.isna(message_text):
                    logging.warning(f"Empty message in row {index + 1}")
                    continue
                    
                messages = self.extract_messages(message_text)
                if not messages:
                    continue
                
                for msg_idx, message in enumerate(messages):
                    try:
                        # Analyze sentiment
                        sentiment_result = self.analyze_sentiment(message)
                        if sentiment_result:
                            df.at[index, 'Google 감정 점수'] = sentiment_result['score']
                            df.at[index, 'Google 감정 강도'] = sentiment_result['magnitude']
                        
                        # Analyze with Perspective API
                        perspective_result = self.analyze_perspective(message)
                        if perspective_result:
                            df.at[index, 'Perspective 유해성'] = perspective_result.get('TOXICITY')
                            df.at[index, 'Perspective 심각한 유해성'] = perspective_result.get('SEVERE_TOXICITY')
                            df.at[index, 'Perspective 정체성 공격'] = perspective_result.get('IDENTITY_ATTACK')
                            df.at[index, 'Perspective 모욕'] = perspective_result.get('INSULT')
                            df.at[index, 'Perspective 욕설'] = perspective_result.get('PROFANITY')
                            df.at[index, 'Perspective 위협'] = perspective_result.get('THREAT')
                        
                        logging.info(f"Processed row {index + 1}, message {msg_idx + 1}/{len(messages)}")
                        
                    except Exception as e:
                        logging.error(f"Error processing message {msg_idx + 1} in row {index + 1}: {str(e)}")
                        continue
                
            except Exception as e:
                logging.error(f"Error processing row {index + 1}: {str(e)}")
                continue
        
        return df
    
    def process_file(self, input_file: str) -> Optional[pd.DataFrame]:
        """Process a CSV file containing messages."""
        try:
            df = pd.read_csv(input_file, encoding='utf-8')
            logging.info(f"Successfully read {len(df)} rows from {input_file}")
            
            # Determine message column name
            message_column = None
            for col in self.config.message_columns:
                if col in df.columns:
                    message_column = col
                    break
            
            if not message_column:
                logging.error(f"Could not find message column in {input_file}")
                return None
            
            logging.info(f"Using message column: {message_column}")
            return self.process_dataframe(df, message_column)
            
        except Exception as e:
            logging.error(f"Error processing file {input_file}: {str(e)}")
            return None

def analyze_files(input_files: Union[str, List[str]], api_key: str, output_dir: str = 'output') -> None:
    """Analyze one or more files and save results."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert single file to list
    if isinstance(input_files, str):
        input_files = [input_files]
    
    # Initialize analyzer
    config = AnalysisConfig(api_key=api_key)
    analyzer = SentimentAnalyzer(config)
    
    # Process all files
    for input_file in input_files:
        logging.info(f"\nProcessing file: {input_file}")
        results_df = analyzer.process_file(input_file)
        
        if results_df is not None:
            # Create timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(input_file)
            output_file = f'{output_dir}/{os.path.splitext(filename)[0]}_analysis_{timestamp}.csv'
            
            # Save to output file
            results_df.to_csv(output_file, encoding='utf-8-sig', index=False)
            logging.info(f"Results saved to {output_file}")
        else:
            logging.error(f"Failed to process file: {input_file}")

def main():
    """Main function for command-line usage."""
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        logging.error("GOOGLE_API_KEY not found in .env file")
        print("Error: GOOGLE_API_KEY not found in .env file")
        print("Please create a .env file with your Google Cloud API key")
        print("Example: GOOGLE_API_KEY=your-api-key-here")
        return
    
    # Get input files from input directory
    input_dir = 'input'
    input_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith('.csv')]
    logging.info(f"Found {len(input_files)} CSV files to process")
    
    # Analyze files
    analyze_files(input_files, api_key)

if __name__ == "__main__":
    main() 
# Korean Sentiment and Toxicity Analyzer

A Python library for analyzing sentiment and toxicity in Korean text using Google Cloud APIs.

## Features

- Sentiment analysis using Google Cloud Natural Language API
- Toxicity analysis using Perspective API
- Support for multiple message formats in CSV files
- Rate limiting and retry mechanisms for API calls
- Comprehensive error handling and logging

## Installation

1. Clone the repository:
```bash
git clone https://github.com/cloudnative-app/sentiment_analyze.git
cd sentiment_analyze
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```
GOOGLE_API_KEY=your-google-cloud-api-key
```

## Usage

### As a Library

```python
from sentiment_analyzer import SentimentAnalyzer, AnalysisConfig

# Initialize analyzer
config = AnalysisConfig(
    api_key="your-api-key",
    perspective_api_delay=1.1,  # Delay between API calls
    max_retries=3,              # Maximum retry attempts
    retry_delay=5,              # Delay between retries
    message_columns=["message_column1", "message_column2"]  # Custom message columns
)
analyzer = SentimentAnalyzer(config)

# Process a single file
results_df = analyzer.process_file("path/to/your/file.csv")

# Process a DataFrame
import pandas as pd
df = pd.read_csv("path/to/your/file.csv")
results_df = analyzer.process_dataframe(df, "message_column")
```

### Command Line

```bash
python sentiment_analyzer.py
```

The script will:
1. Look for CSV files in the `input` directory
2. Process each file using both sentiment and toxicity analysis
3. Save results to the `output` directory with timestamps

## Configuration

The `AnalysisConfig` class allows you to customize various aspects of the analysis:

- `api_key`: Your Google Cloud API key
- `perspective_api_delay`: Delay between Perspective API calls (default: 1.1 seconds)
- `max_retries`: Maximum number of retry attempts for failed API calls (default: 3)
- `retry_delay`: Delay between retry attempts (default: 5 seconds)
- `message_columns`: List of possible message column names in your CSV files

## Output

The analyzer adds the following columns to your data:

- `Google 감정 점수`: Sentiment score (-1.0 to 1.0)
- `Google 감정 강도`: Sentiment magnitude (0.0 to ∞)
- `Perspective 유해성`: Toxicity score (0.0 to 1.0)
- `Perspective 심각한 유해성`: Severe toxicity score (0.0 to 1.0)
- `Perspective 정체성 공격`: Identity attack score (0.0 to 1.0)
- `Perspective 모욕`: Insult score (0.0 to 1.0)
- `Perspective 욕설`: Profanity score (0.0 to 1.0)
- `Perspective 위협`: Threat score (0.0 to 1.0)

## Requirements

- Python 3.7+
- pandas
- google-cloud-language
- requests
- python-dotenv

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 
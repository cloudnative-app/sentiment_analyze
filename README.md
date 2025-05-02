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

---

# 한국어 감정 및 유해성 분석기

Google Cloud API를 사용하여 한국어 텍스트의 감정과 유해성을 분석하는 Python 라이브러리입니다.

## 주요 기능

- Google Cloud Natural Language API를 사용한 감정 분석
- Perspective API를 사용한 유해성 분석
- 다양한 형식의 CSV 파일 지원
- API 호출에 대한 속도 제한 및 재시도 메커니즘
- 상세한 오류 처리 및 로깅

## 설치 방법

1. 저장소 복제:
```bash
git clone https://github.com/cloudnative-app/sentiment_analyze.git
cd sentiment_analyze
```

2. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

3. `.env` 파일에 API 키 설정:
```
GOOGLE_API_KEY=your-google-cloud-api-key
```

## 사용 방법

### 라이브러리로 사용하기

```python
from sentiment_analyzer import SentimentAnalyzer, AnalysisConfig

# 분석기 초기화
config = AnalysisConfig(
    api_key="your-api-key",
    perspective_api_delay=1.1,  # API 호출 간 지연 시간
    max_retries=3,              # 최대 재시도 횟수
    retry_delay=5,              # 재시도 간 지연 시간
    message_columns=["message_column1", "message_column2"]  # 사용자 정의 메시지 컬럼
)
analyzer = SentimentAnalyzer(config)

# 단일 파일 처리
results_df = analyzer.process_file("path/to/your/file.csv")

# DataFrame 처리
import pandas as pd
df = pd.read_csv("path/to/your/file.csv")
results_df = analyzer.process_dataframe(df, "message_column")
```

### 명령줄에서 사용하기

```bash
python sentiment_analyzer.py
```

스크립트는 다음 작업을 수행합니다:
1. `input` 디렉토리에서 CSV 파일을 찾습니다
2. 각 파일에 대해 감정 및 유해성 분석을 수행합니다
3. 결과를 타임스탬프와 함께 `output` 디렉토리에 저장합니다

## 설정

`AnalysisConfig` 클래스를 통해 분석의 다양한 측면을 사용자 정의할 수 있습니다:

- `api_key`: Google Cloud API 키
- `perspective_api_delay`: Perspective API 호출 간 지연 시간 (기본값: 1.1초)
- `max_retries`: API 호출 실패 시 최대 재시도 횟수 (기본값: 3회)
- `retry_delay`: 재시도 간 지연 시간 (기본값: 5초)
- `message_columns`: CSV 파일에서 사용할 수 있는 메시지 컬럼 이름 목록

## 출력 결과

분석기는 데이터에 다음 컬럼을 추가합니다:

- `Google 감정 점수`: 감정 점수 (-1.0 ~ 1.0)
- `Google 감정 강도`: 감정 강도 (0.0 ~ ∞)
- `Perspective 유해성`: 유해성 점수 (0.0 ~ 1.0)
- `Perspective 심각한 유해성`: 심각한 유해성 점수 (0.0 ~ 1.0)
- `Perspective 정체성 공격`: 정체성 공격 점수 (0.0 ~ 1.0)
- `Perspective 모욕`: 모욕 점수 (0.0 ~ 1.0)
- `Perspective 욕설`: 욕설 점수 (0.0 ~ 1.0)
- `Perspective 위협`: 위협 점수 (0.0 ~ 1.0)

## 요구사항

- Python 3.7 이상
- pandas
- google-cloud-language
- requests
- python-dotenv

## 라이선스

MIT 라이선스

## 기여하기

기여를 환영합니다! Pull Request를 자유롭게 제출해주세요. 
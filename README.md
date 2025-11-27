# 📚 Enhanced Research Assistant

An AI-powered research tool that conducts automated web research, generates comprehensive reports, and compares them against existing documents.
![Preview](./Preview/output.gif)

## Features

- Multi-agent AI research workflow
- Upload PDF/text for comparison
- Automated research planning and execution
- Web search with fact collection
- Generate 5-10 page detailed reports
- Quality assessment and comparison analysis
- Download reports as markdown

## Installation

1. Clone the repository and navigate to it
2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create `.env` file with your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

## Usage

Run the application:

```bash
streamlit run app.py
```

Then:

1. Optionally upload a PDF or text file
2. Enter your research topic
3. Click "Start Research"
4. View results in the three tabs: Research Process, Final Report, Comparison

## Requirements

- Python 3.8+
- OpenAI API Key ([get one here](https://platform.openai.com/api-keys))

## How It Works

Five specialized AI agents collaborate to conduct research:

- **Gap Analysis Agent** - Identifies gaps in existing research
- **Planning Agent** - Creates targeted search queries
- **Research Agent** - Conducts web searches
- **Editor Agent** - Synthesizes findings into a report
- **Comparison Agent** - Compares original and new research

## Troubleshooting

**Missing API Key Error** - Ensure `.env` file contains your OpenAI API key
**Slow Performance** - Research can take 2-5 minutes depending on topic complexity

# Vaccination Data Analysis and Visualization

## Project objective
Analyze global vaccination coverage, disease incidence, reported cases, vaccine introduction and vaccine schedule data. The project follows the requested workflow: **Python data cleaning → SQL database → EDA/analysis → Power BI dashboard**.

The project specification calls for analysis of vaccination trends, disease incidence, regional disparities, vaccine introduction and schedule effects, with interactive Power BI reporting. fileciteturn0file0L29-L58

## Data model
The source specification defines five tables:
- `coverage`
- `incidence_rate`
- `reported_cases`
- `vaccine_introduction`
- `vaccine_schedule`

Their expected fields are described in the supplied project document. fileciteturn0file0L150-L220

## Folder structure
```text
vaccination_data_analysis/
├── data/
│   ├── raw/                 # put source CSV files here
│   └── processed/           # generated cleaned CSVs
├── src/
│   ├── config.py
│   ├── data_cleaning.py
│   ├── load_sql.py
│   ├── eda.py
│   └── run_pipeline.py
├── sql/
│   ├── schema_mysql.sql
│   └── analysis_queries.sql
├── powerbi/
│   └── DAX_measures.txt
├── notebooks/
├── outputs/
├── reports/
├── .env.example
├── requirements.txt
└── README.md
```

## 1. Setup
Windows:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## 2. Add the source data
Download the project dataset from the source listed in the assignment and place the five CSV files in `data/raw/`.

Use these names:
```text
coverage_data.csv
incidence_rate.csv
reported_cases.csv
vaccine_introduction.csv
vaccine_schedule.csv
```

If your downloaded files have different names, either rename them or edit `src/config.py`.

The assignment identifies the source as a Google Drive folder. fileciteturn0file0L144-L146

## 3. Run the complete Python pipeline
From the project root:
```bash
cd src
python run_pipeline.py
```

This:
1. standardizes column names;
2. converts numeric/year fields;
3. trims text;
4. removes exact duplicates;
5. writes cleaned CSVs;
6. loads cleaned tables into the configured SQL database;
7. creates basic EDA charts.

## 4. Database
### Easiest local option
The default `.env` uses:
```text
DATABASE_URL=sqlite:///vaccination.db
```

### MySQL option for Power BI
Install MySQL 8 and create the database using:
```bash
mysql -u root -p < sql/schema_mysql.sql
```

Then set:
```text
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/vaccination_db
```

Run:
```bash
cd src
python run_pipeline.py
```

## 5. Power BI dashboard
Connect Power BI to the MySQL database and import:
- coverage
- incidence_rate
- reported_cases
- vaccine_introduction
- vaccine_schedule

Create relationships primarily through:
- `coverage[code]` ↔ country code
- `coverage[year]` ↔ year
- `incidence_rate[code]` ↔ country code
- `reported_cases[code]` ↔ country code

For a production-quality model, create shared dimensions such as `DimCountry`, `DimYear`, `DimDisease`, and `DimVaccine`, then use a star schema.

The assignment specifically asks for interactive filters/slicers, maps, trend charts, scatter plots and KPI indicators. fileciteturn0file0L49-L58

## Power BI pages

### Page 1 — Global Vaccination Overview
KPI cards:
- Average Coverage %
- Total Doses
- Total Reported Cases
- Coverage Gap to 95%

Charts:
- Coverage trend by year
- Coverage by country map
- Coverage by antigen
- Top/bottom countries

### Page 2 — Disease Impact
- Disease cases by year
- Incidence rate by disease
- Vaccination coverage vs incidence scatter
- Country and disease slicers

### Page 3 — Vaccine Introduction
- First introduction year by WHO region
- Countries introduced by vaccine
- Introduction trend
- WHO region slicer

### Page 4 — Vaccination Schedule
- Schedule rounds
- Target population
- Age administered
- Vaccine and country filters

### Page 5 — Equity / Gap Analysis
- Countries below 95%
- Gap to 95% by country
- WHO-region comparison
- Low-coverage priority table


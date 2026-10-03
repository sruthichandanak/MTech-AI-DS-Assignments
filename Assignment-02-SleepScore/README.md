# Assignment 02: Sleep Score and Mental Health Estimator


## Dataset Overview (`Sleep_Efficiency.csv`)
The dataset contains **452 rows** of sleep and lifestyle metrics, including:
* **Demographics & Lifestyle:** Age, Gender, Smoking status, Exercise frequency, Caffeine & Alcohol consumption.
* **Timing & Duration:** Bedtime, Wakeup time, and Sleep duration (Total Sleep Time).
* **Core Sleep Metrics:** Sleep efficiency, REM/Deep/Light sleep percentages, and Awakenings count.

---

## Core Methodology & Agent Architecture
* **Agent Type:** **Model-Based Agent**. It evaluates time-series environment states (duration, efficiency, interruptions) and maps them onto a single utility performance measure (the Sleep Score).

### The Scoring Formula (0 to 100)
$$	{Sleep Score} = 0.40(	{Duration Score}) + 0.40(	{Efficiency Score}) + 0.20(	{Interruption Score})$$

1. **Duration Score (40% Weight):** Optimal target is **7 to 9 hours** (100 points). Deducts 25 points per hour of deviation outside this range.
2. **Efficiency Score (40% Weight):** Target is **$\ge 85\%$** sleep efficiency, scaled and capped at 100 points.
3. **Interruption Score (20% Weight):** Starts at 100 points and deducts **15 points per awakening**.

### Recalibrated Mental Health Estimation Thresholds
* **Good and Low Stress:** Sleep Score $\ge 85$
* **Moderate Risk and Fatigue:** Sleep Score between $70$ and $84.99$
* **High Risk and Poor Mental Health:** Sleep Score $< 70$

---

## How to Run the Code

### Prerequisites
Make sure you have Python 3 installed on your system.

### 1. Set Up a Virtual Environment (Recommended on macOS/Linux)
Open your terminal in the project directory and run:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
Install **pandas** inside your virtual environment:
```bash
pip install pandas
```

### 3. Run the Python Script
Execute the script to process the data, calculate scores, print the breakdown, and generate the output CSV:
```bash
python3 sleepscore.py
```

---

## File Structure
* `Sleep_Efficiency.csv`: The raw input dataset.
* `sleepscore.py`: The main Python script containing the rule-based scoring logic.
* `sleep_score_output.csv`: The processed output file containing individual sleep scores and mental health classifications.
* `README.md`: Project documentation and guide.

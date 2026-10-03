import pandas as pd

# 1.Loading the dataset
df = pd.read_csv('Sleep_Efficiency.csv')
print("Original data")
print(df.head(3))


# Calculating duaration score
# Sleep Duration of 7 to 9 hours is good
# every deviation is penalised by decreasing 25 points for every hour of deviation

def score_duration(hours):
    if hours >= 7 and hours <= 9:
        return 100
    else:
        if hours < 7 or hours > 9:
            d = min(abs(hours - 7), abs(hours - 9))
        else:
            return 0
        return max(0, 100 - (d * 25))
    
# score efficiency
# converts decimal efficiency to percentage
# scales the percentage against target of 85% capping max score at 100 and min at 0

def score_efficiency(eff):
    p = eff * 100
    return min(100, max(0, (p/85)*100))

# no of awakeings
# if missing value, then default value is filled with 70(middle score)
# penality of 15 points for every awakening

def score_awakenings(awakenings):
    if pd.isna(awakenings):
        return 70
    return max(0, 100 - (awakenings * 15))

# these functions are applied to every single row in the dataset

df['duration_score'] = df['Sleep duration'].apply(score_duration)
df['efficiency_score'] = df['Sleep efficiency'].apply(score_efficiency)
df['interruption_score'] = df['Awakenings'].apply(score_awakenings)

# SLEEP SCORE CALCULATION

df['Sleep_Score'] = (0.40 * df['duration_score'] +  0.40 * df['efficiency_score'] + 0.20 * df['interruption_score'])

# MENTAL HEALTH ESTIMATION
# Estimate mental health based on the final score

def estimate_mental_health(score):
    if score >= 85:
        return "Good and Low Stress"
    elif score >= 70:
        return "Moderate Risk and Fatigue"
    else:
        return "High Risk and Poor Mental Health"

df['Estimated_Mental_Health'] = df['Sleep_Score'].apply(estimate_mental_health)

# Print the first few rows to see your new scores right in the terminal
print("\nProcessed Data")
print(df[['ID', 'Sleep duration', 'Sleep efficiency', 'Awakenings', 'Sleep_Score', 'Estimated_Mental_Health']].head(10))

# Save the final results to a new CSV file
df.to_csv('sleep_score_output.csv', index=False)
print("\nSuccess! Results saved to 'sleep_score_output.csv'.")



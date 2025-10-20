from scipy.stats import chi2_contingency
import numpy as np

# ==============================================================================
# 1. INPUT YOUR A/B TEST RESULTS FROM SNOWFLAKE QUERY
# ==============================================================================

# Version A (e.g., blue button)
visitors_A = 184
conversions_A = 11

# Version B (e.g., green button)
visitors_B = 154
conversions_B = 8

# ==============================================================================
# 2. CALCULATE AND BUILD CONTINGENCY TABLE
# ==============================================================================

# Calculate non-converted users for each group
non_conversions_A = visitors_A - conversions_A
non_conversions_B = visitors_B - conversions_B

# Build 2x2 contingency table for Chi-Squared test
# Format: [[Group A Converted, Group A Not-Converted], 
#          [Group B Converted, Group B Not-Converted]]
observed_data = np.array([
    [conversions_A, non_conversions_A],
    [conversions_B, non_conversions_B]
])

# ==============================================================================
# 3. PERFORM CHI-SQUARED TEST AND OUTPUT RESULTS
# ==============================================================================

# Perform Chi-Squared test of independence
chi2, p_value, _, _ = chi2_contingency(observed_data)

print("================= A/B Test Significance Results =================")
print(f"Data:")
print(f"  - Version A: {conversions_A} conversions out of {visitors_A} visitors (Rate: {conversions_A/visitors_A:.2%})")
print(f"  - Version B: {conversions_B} conversions out of {visitors_B} visitors (Rate: {conversions_B/visitors_B:.2%})")
print("\nContingency Table:")
print("              Converted   Not-Converted")
print(f"Version A       {observed_data[0][0]:^9}   {observed_data[0][1]:^13}")
print(f"Version B       {observed_data[1][0]:^9}   {observed_data[1][1]:^13}")
print("\n-----------------------------------------------------------------")
print(f"Chi-Squared Statistic: {chi2:.4f}")
print(f"P-value: {p_value:.4f}")
print("-----------------------------------------------------------------")

# Interpret statistical significance results
alpha = 0.05  # 95% confidence level (standard for A/B testing)
if p_value < alpha:
    print("\nConclusion: The result is statistically significant.")
    print("We can reject the null hypothesis. There is a real difference in conversion rates between Version A and Version B.")
else:
    print("\nConclusion: The result is not statistically significant.")
    print("We do not have enough evidence to reject the null hypothesis. The observed difference could be due to random chance.")
print("=================================================================\n")
# Local PySpark ETL Script for A/B Test Project (Final Version with Manual JARs)

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, expr

# ==============================================================================
# 1. CONFIGURE ALL CREDENTIALS AND IDENTIFIERS (All configurations centralized here)
# ==============================================================================

# -- BigQuery Configuration --
gcp_keyfile_name = "xxxxxx.json"
bq_project = "ab-test-analytics-xxxxx"
bq_dataset = "analytics_xxxxx"
# Explicitly query yesterday's table to avoid table not found errors due to GA4 export delays
bq_table = "events_xxxxxxx" 

# -- MongoDB Configuration --
mongo_connection_string = "mongodb+srv://jeremiahliulc_db_user:xxxxxxxxxx@ab-test-cluster.vo4w9me.mongodb.net/?retryWrites=true&w=majority&appName=AB-test-cluster"

# -- Snowflake Configuration --
snowflake_user = "xxxxxx"
snowflake_password = "xxxxxxxxx"
snowflake_account = "xxxxxxxx" 
snowflake_warehouse = "COMPUTE_WH"
snowflake_database = "AB_TEST_PROJECT"
snowflake_schema = "PUBLIC"

# ==============================================================================
# 2. INITIALIZE SPARKSESSION (Final Simplified Version)
# ==============================================================================

# Set HADOOP_HOME environment variable for Windows
os.environ['HADOOP_HOME'] = os.path.join(r'D:\spark\spark-3.5.7-bin-hadoop3', 'hadoop')

# Define folder containing downloaded local JAR files
jars_folder = "jars"

# Get full paths to all .jar files in the jars folder
jar_files = [os.path.abspath(os.path.join(jars_folder, f)) for f in os.listdir(jars_folder) if f.endswith(".jar")]

print("Loading the following local JAR files:")
for jar in jar_files:
    print(f"- {os.path.basename(jar)}")

# Build Spark session with required configurations
spark = SparkSession.builder \
    .appName("LocalABTestETL-Final") \
    .config("spark.jars", ",".join(jar_files)) \  # Add all required connector JARs
    .config("spark.driver.memory", "2g") \        # Allocate sufficient memory
    .getOrCreate()

# Configure BigQuery connector to use your key file
spark.conf.set("credentialsFile", os.path.abspath(gcp_keyfile_name))

print("✅ SparkSession initialized successfully!")

# ==============================================================================
# 3. READ AND TRANSFORM GA4 QUANTITATIVE DATA FROM BIGQUERY
# ==============================================================================

print("\n[Phase 1/3] Reading data from BigQuery...")
# Read raw GA4 event data from BigQuery
df_ga4_raw = spark.read \
  .format("bigquery") \
  .option("table", f"{bq_project}.{bq_dataset}.{bq_table}") \
  .option("parentProject", bq_project) \
  .load()

# Extract and flatten nested event parameters using dot notation for MAP/STRUCT
df_ga4_flat = df_ga4_raw.select(
    col("user_pseudo_id"),                            # Anonymous user identifier
    col("event_name"),                                # Event type (page_view, purchase_click, etc.)
    col("event_params.test_version.string_value").alias("test_version")  # Extract A/B test version
)

# Filter out records without test version assignment
df_ga4_filtered = df_ga4_flat.filter(col("test_version").isNotNull())

# Identify unique visitors (users who viewed the page)
df_visitors = df_ga4_filtered.filter(col("event_name") == "page_view").select("user_pseudo_id", "test_version").distinct()

# Identify conversions (users who clicked purchase button)
df_conversions = df_ga4_filtered.filter(col("event_name") == "purchase_click").select("user_pseudo_id").withColumn("converted", expr("1")).distinct()

# Join visitors with conversions to create final A/B test results
df_ab_test_results = df_visitors.join(
    df_conversions,
    df_visitors.user_pseudo_id == df_conversions.user_pseudo_id,
    "left_outer"  # Keep all visitors, even those who didn't convert
).select(
    df_visitors.user_pseudo_id,
    df_visitors.test_version,
    col("converted").isNotNull().alias("is_converted")  # Boolean flag for conversion
)

print("✅ Quantitative A/B test results data prepared:")
df_ab_test_results.show(5)

# ==============================================================================
# 4. READ AND TRANSFORM QUALITATIVE FEEDBACK DATA FROM MONGODB
# ==============================================================================

print("\n[Phase 2/3] Reading data from MongoDB...")
# Read user feedback data from MongoDB collection
df_user_feedback = spark.read \
    .format("mongodb") \
    .option("connection.uri", mongo_connection_string) \
    .option("database", "ab_test_project") \
    .option("collection", "user_comments") \
    .load()

# Select and clean relevant fields from feedback data
df_user_feedback_clean = df_user_feedback.select(
    col("user_pseudo_id"),                    # User identifier for joining
    col("test_version"),                      # A/B test version assignment
    col("comment_text"),                      # User's textual feedback
    col("star_rating"),                       # 1-5 star rating
    col("tags"),                              # Array of feedback tags
    col("time_to_convert_seconds")            # Time taken to complete conversion
)

print("✅ Qualitative user feedback data prepared:")
df_user_feedback_clean.show(5)

# ==============================================================================
# 5. WRITE PROCESSED DATA TO SNOWFLAKE DATA WAREHOUSE
# ==============================================================================

print("\n[Phase 3/3] Writing data to Snowflake...")

# Snowflake connection configuration
sf_options = {
    "sfURL": f"{snowflake_account}.snowflakecomputing.com",
    "sfUser": snowflake_user,
    "sfPassword": snowflake_password,
    "sfDatabase": snowflake_database,
    "sfSchema": snowflake_schema,
    "sfWarehouse": snowflake_warehouse
}

# Write A/B test results to Snowflake
(df_ab_test_results.write
  .format("snowflake")
  .options(**sf_options)
  .option("dbtable", "AB_TEST_RESULTS")
  .mode("overwrite")  # Replace existing table
  .save())

print("✅ Successfully wrote A/B test results to Snowflake table 'AB_TEST_RESULTS'")

# Write user feedback data to Snowflake
(df_user_feedback_clean.write
  .format("snowflake")
  .options(**sf_options)
  .option("dbtable", "USER_FEEDBACK")
  .mode("overwrite")  # Replace existing table
  .save())
  
print("✅ Successfully wrote user feedback data to Snowflake table 'USER_FEEDBACK'")

# ==============================================================================
# 6. STOP SPARKSESSION AND CLEAN UP
# ==============================================================================
spark.stop()
print("\n🎉 ETL pipeline completed successfully!")
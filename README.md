graph TD;
    subgraph "数据源 (Sources)"
        GA4[Google Analytics 4]
        Mongo[MongoDB Atlas]
    end

    subgraph "提取 & 加载 (Extract & Load)"
        BigQuery[Google BigQuery]
        GCS[Google Cloud Storage]
        LocalFile[本地 JSON 文件]
        Snowflake[Snowflake 云数据仓库]

        GA4 -- 每日导出 --> BigQuery;
        BigQuery -- 导出为 CSV --> GCS;
        Mongo -- mongoexport --> LocalFile;
        GCS -- Storage Integration --> Snowflake;
        LocalFile -- UI 上传 --> Snowflake;
    end

    subgraph "转换 & 分析 (Transform & Analyze)"
        T_SQL[Snowflake SQL]
        Py[Python (SciPy)]

        Snowflake -- 在仓库内转换 --> T_SQL;
        T_SQL -- 导出结果 --> Py;
    end

    subgraph "可视化 (Visualize)"
        PBI[Power BI]
        Tab[Tableau]

        Snowflake -- 直接连接 --> PBI;
        Snowflake -- 导出 CSV 连接 --> Tab;
    end

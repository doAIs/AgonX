"""执行数据库迁移脚本

使用docker/mysql目录下的升级脚本
"""
import pymysql
import sys
import os

def run_migration():
    try:
        # 连接数据库
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='agonx',
            password='agonx_password',
            database='agonx',
            charset='utf8mb4'
        )
        
        print("✅ 数据库连接成功")
        
        # 读取SQL文件（使用docker/mysql目录下的脚本）
        sql_file = '../docker/mysql/upgrade_v1.1_rich_media.sql'
        if not os.path.exists(sql_file):
            print(f"❌ 升级脚本不存在: {sql_file}")
            sys.exit(1)
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句（按分号分割）
        sql_statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        
        cursor = connection.cursor()
        
        # 执行每条SQL语句
        for i, statement in enumerate(sql_statements, 1):
            if statement:
                try:
                    print(f"执行语句 {i}/{len(sql_statements)}...")
                    cursor.execute(statement)
                    print(f"  ✅ 成功")
                except Exception as e:
                    print(f"  ⚠️ 警告: {str(e)}")
        
        connection.commit()
        print("\n🎉 数据库迁移完成！")
        
        # 验证表是否创建成功
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\n当前数据库表: {len(tables)} 个")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()

"""检查数据库表结构"""
import pymysql

def check_structure():
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='agonx',
            password='agonx_password',
            database='agonx',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 检查documents表结构
        print("=" * 60)
        print("检查 documents 表结构")
        print("=" * 60)
        cursor.execute("DESCRIBE documents")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]:<30} {col[1]:<20} {col[2]:<10} {col[3]}")
        
        # 检查是否存在富媒体相关表
        print("\n" + "=" * 60)
        print("检查富媒体相关表")
        print("=" * 60)
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        rich_media_tables = ['document_pages', 'document_elements', 'document_chunks', 'ocr_tasks']
        for table_name in rich_media_tables:
            exists = any(table_name in t for t in tables)
            status = "✅ 存在" if exists else "❌ 不存在"
            print(f"  {table_name:<30} {status}")
            
            if exists:
                cursor.execute(f"DESCRIBE {table_name}")
                cols = cursor.fetchall()
                print(f"    字段数: {len(cols)}")
        
        # 检查现有字段
        print("\n" + "=" * 60)
        print("检查 documents 表的富媒体字段")
        print("=" * 60)
        cursor.execute("DESCRIBE documents")
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]
        
        rich_fields = ['content_type', 'page_count', 'has_images', 'has_tables']
        for field in rich_fields:
            exists = field in column_names
            status = "✅ 存在" if exists else "❌ 不存在"
            print(f"  {field:<30} {status}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_structure()

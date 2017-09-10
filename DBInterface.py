
import pymysql
import json

class DBInterface:
    cnx = None
    cursor = None

    def __init__(self):
        self.cnx = pymysql.connect(user='root', passwd='2hourcommute',
                                            host='db.emag-bot.com', port=3306,
                                            database='ebot')
        self.cursor = self.cnx.cursor()
        
        print("Connection ok.")

    def QueryForLabels(self, labels = []):
        print(labels)
        query = (
            "SELECT DISTINCT label.name, label.image_id, image.id, image.raw, product.id "
            "FROM label, image, product "
            "WHERE label.name IN (%s) "
            "AND label.image_id=image.id AND image.product_id=product.id "
            "GROUP BY product.name"
        )

        in_p=', '.join(map(lambda x: '%s', labels))
        query = query % in_p
        print(query)
        self.cursor.execute("SET sql_mode = ''")
        self.cursor.execute(query, labels)

        return self.cursor.fetchall()

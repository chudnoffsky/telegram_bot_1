import feedparser


def feed_parser():
    NewsRssFeed = {
        'РосРеестр': 'https://rosreestr.ru/site/rss/', 
        'Федеральная Налоговая Служба': 'https://www.nalog.ru/rn62/rss/', 
        'Бизнес': 'https://www.liga.net/tech/own-business/rss.xml', 
        'Технологии': 'https://www.liga.net/tech/technology/rss.xml'
    }
    # выбранные рсс источники

    message = dict()
    for key in NewsRssFeed.keys():
        current_news = feedparser.parse(NewsRssFeed[key]).entries[0]
        message[key] = current_news.title + '\n' + current_news.link
    return message

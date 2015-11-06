[Тут статья про то как писать на perl.] (http://citforum.ru/internet/perl/ten_tips/) И есть упоминание про автофрматирование текста. Возможно будет полезно.


###Пример класса коннектор, тут для SMTP, главное чтобы были методы __enter__ __exit__.


      class ServerConnect(object):

        """
            class for with. Create connect to smtp server.
        """
        def __init__(self):
            self.server = None
            self.smtppasswd = mailconfig.smtppasswd
            self.smtpservername = mailconfig.smtpservername
            self.port='465'
            self.myadress = mailconfig.myaddress
        def __enter__(self):
            """ On enter in with """
            self.server = smtplib.SMTP_SSL(self.smtpservername, self.port)
            return self.server
        def __exit__(self, _type, value, traceback):
            """ On exit of with """
            self.server.quit()


      self.server_connect = ServerConnect()
      with self.server_connect as server:
        server.sendmail(self._from, self.to, top.as_string())


  Экономия в пару строк, зато не нужно следить за закрытием соединения)

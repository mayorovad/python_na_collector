#Описание формата вывода
Вся полученная информация хранится в **SantriParser.collector_report**, который возвращает метод **SantriClient.get_report()**

| Название ключа | Известные значения | Подробное описание |
|---|---|---|
| PS[N] STATUS | OK / Failure / No Power | Состояние блока питания N |
| BATTERY[N] STATUS | OK / Expiring / Failure / Charging | Состояние батареи N |
| SFP[N] STATUS | OK / Failure | Small Form-factor Pluggable - используются для присоединения платы сетевого устройства к оптическому волокну |
| OST0 | OK | Object Storage Device - абстрактное устройство хранения объектов (используется в Lustre) |
| BACKUP | OK | Раздел для резервных копий |
| GFS0 | OK | Раздел с файловой системой GFS (Google File System) - ??? |
| SMC1 | OK | Используется с tape and medium changer devices. Единственное упоминание нашел [здесь](https://books.google.ru/books?id=CbLEAgAAQBAJ&pg=PA303&dq=SMC1+ibm&hl=ru&sa=X&ved=0CCMQ6AEwAGoVChMI776Wu8mFyQIVQlgsCh09IAGW#v=onepage&q=SMC1%20ibm&f=false)
| MDT0 | OK | Metadata target - хранит метаданные о пространстве имен, например имена файлов, каталогов, права доступа, а также карту размещения файлов |
| VM_STORAGE | OK | Том для интеграции с VMware? |

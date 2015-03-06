# crecabullet

crecabullet is push newer your credit-card's utilization with [pushbullet](https://www.pushbullet.com/).

## requirements

* peewee
* pyquery
* pushbullet.py

And make pushbullet account.

## Ready

```shell
$ # sudo yum install gcc libxml2-devel libxslt-devel # Option commands as necessary
$ sudo easy_install pip
$ sudo pip install peewee pyquery pushbullet.py
```

## Installment

```shell
$ cd /path/to/dir
$ git clone https://github.com/takudo/crecabullet.git
$ cd crecabullet
$ mv app.cfg.template app.cfg
$ vi app.cfg
# edit your information

$ crontab -e
0 * * * * cd /path/to/dir/crecabullet && python main.py
```

## Support Service

* [三井住友Visaカード Vpass](https://www.smbc-card.com/mem/vps/index.jsp)
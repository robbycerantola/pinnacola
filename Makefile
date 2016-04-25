.PHONY: po mo

po:
	xgettext -Lpython --output=messages.pot main.py pinnacola1.kv
	msgmerge --update --no-fuzzy-matching --backup=off po/en.po messages.pot
	msgmerge --update --no-fuzzy-matching --backup=off po/it.po messages.pot

mo:
	mkdir -p data/locales/en/LC_MESSAGES
	mkdir -p data/locales/it/LC_MESSAGES
	msgfmt -c -o data/locales/en/LC_MESSAGES/pinnacola.mo po/en.po
	msgfmt -c -o data/locales/it/LC_MESSAGES/pinnacola.mo po/it.po
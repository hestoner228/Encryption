# ZTPNG Converter

Конвертер в обе стороны:

- `PNG -> текстовый .ztpng`
- `.ztpng -> PNG`

## Запуск

Нужен Python 3.9+.

### Режим консоли (как ты просил)

Просто запускаешь без аргументов:

```bash
python ztpng.py
```

И вводишь команды:

- `"C:\путь\к\картинке.png" in ztpng` (PNG -> ZTPNG)
- `"C:\путь\к\файлу.ztpng" in png` (ZTPNG -> PNG)

Выходной файл создаётся рядом, с тем же именем, но другим расширением.

### Режим команд (старый вариант)

```bash
python ztpng.py encode input.png output.ztpng
python ztpng.py decode output.ztpng restored.png
```

Формат `.ztpng` содержит:

- сигнатуру `ZTPNG1`
- исходное имя файла
- размер в байтах
- SHA256
- base64-данные картинки

При декодировании проверяются размер и SHA256 (защита от поврежденного текста).

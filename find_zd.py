import re

with open(r'C:\Users\shenw\Documents\New project\市场稽核部重点工作看板-06101350.html', 'r', encoding='utf-8') as f:
    content = f.read()

zd_start = content.find('var ZD =')
zd_end = content.find('</script>', zd_start)
print(f"ZD starts at char: {zd_start}")
print(f"ZD ends at char: {zd_end}")
print(f"ZD JSON length: {zd_end - zd_start}")
print(f"Total file length: {len(content)}")

# Show a small snippet around the start
print(f"\nContext around ZD start:")
print(repr(content[zd_start:zd_start+100]))

# Count occurrences of '</script>'
script_end_count = content.count('</script>')
print(f"\nTotal </script> count: {script_end_count}")

# Find all </script> positions
for i, m in enumerate(re.finditer(r'</script>', content)):
    if m.start() > zd_start - 100:
        print(f"</script> #{i} at char {m.start()}")

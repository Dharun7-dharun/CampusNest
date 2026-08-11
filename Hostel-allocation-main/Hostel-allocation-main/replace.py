import re

with open('frontend_v3.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('<title>HostelAI — Premium Accommodation</title>', '<title>CampusNest — Premium Accommodation</title>')
text = text.replace('<title>CampusNest  Premium Accommodation</title>', '<title>CampusNest — Premium Accommodation</title>')

home_svg = '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>'

text = re.sub(r'<div class="logo">.*?Hostel<span>AI</span></div>', f'<div class="logo" style="display:flex; align-items:center;">{home_svg}Campus<span>Nest</span></div>', text, flags=re.DOTALL)

text = text.replace('HostelAI', 'CampusNest')
text = text.replace('hostel room allocation', 'campus room allocation')
text = text.replace('Hostel Application Form', 'CampusNest Application Form')
text = text.replace('Hostel Allocation Letter', 'CampusNest Allocation Letter')
text = text.replace('hostel room.', 'room in CampusNest.')
text = text.replace('Hostel Warden', 'CampusNest Warden')
text = text.replace('Hostel Announcements', 'CampusNest Announcements')
text = text.replace('hostel application', 'CampusNest application')
text = text.replace('hostel fees', 'CampusNest fees')

with open('frontend_v3.html', 'w', encoding='utf-8') as f:
    f.write(text)

with open('main.py', 'r', encoding='utf-8') as f:
    main_text = f.read()

main_text = main_text.replace('HostelAI', 'CampusNest')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_text)

print('Done')

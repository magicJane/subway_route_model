from string import Template
import codecs
import webbrowser

# 将subway_route_template.html文件中的${stop_pairs}替换为stop_pairs.txt文件中所有站点对 （167*166），并保存为subway_route.html
input_path = "subway_route_template.html"
output_path = "subway_route.html"

stop_pairs_path = "stop_pairs.txt"


with codecs.open(stop_pairs_path, 'r', 'utf-8') as f:
    stop_pairs = f.read()                    

para = {"stop_pairs": stop_pairs}

with codecs.open(input_path, 'r', 'utf-8') as f:
    model = f.read()
    model_new = Template(model).substitute(para)
    with codecs.open(output_path, 'w', 'utf-8') as o:
        o.write(model_new)

print("Complete substitute stop_pairs")

# 使用默认浏览器打开本地的subway_route.html文件
webbrowser.open("subway_route.html")
print("Scraping Completed...")


    



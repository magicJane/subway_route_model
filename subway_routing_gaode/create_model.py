from string import Template
import codecs
import webbrowser

stops_path = 'subway_stop_names.csv'
input_path = "subway_route_template.html"
output_path = "subway_route.html"

    
def main():
    
    # 创建 stop_pairs
    stops = []
    with codecs.open(stops_path, 'r', 'utf-8') as f:
        for line in f:
            stops.append(line.strip())

    stop_pairs = []
    for start in stops:
        for end in stops:
            if (start != end):
                stop_pairs.append("[{ keyword: '%s（地铁站）',city:'深圳' },{ keyword: '%s（地铁站）',city:'深圳' }]"%(start, end))
    
    stop_pairs = "[%s]"%",".join(stop_pairs)

    para = {"stop_pairs": stop_pairs}

    with codecs.open(input_path, 'r', 'utf-8') as f:
        model = f.read()
        model_new = Template(model).substitute(para)
        with codecs.open(output_path, 'w', 'utf-8') as o:
            o.write(model_new)

    print("Complete substitute stop_pairs")


    # 使用默认浏览器打开本地的subway_route.html文件
    webbrowser.open("subway_route.html")

if __name__ == '__main__':
    main()



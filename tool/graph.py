from graphviz import Digraph
import re

f = open('../beat_ecu_stock.asm', 'r').read()

code_start_index = f.find('code_start')
vectors = f[:code_start_index]
codes = f[code_start_index:]
# labels = list()
labels = list(map(lambda x: re.match(r'([A-z_0-9]*):\s*', x).groups()[0], filter(lambda x: re.match(r'([A-z_0-9]*):\s*', x) ,codes.splitlines())))

print(labels)

graph = Digraph(format='svg', graph_attr={'splines': 'ortho'})
for i, l in enumerate(labels):
    graph.node(l)

    m = re.search(r'^%s:' % l, codes, flags=re.MULTILINE)
    label_start = m.start()
    if i == len(labels) - 1:
        jmp_search_target = codes[label_start:]
    else:
        m = re.search(r'^%s:' % labels[i + 1], codes, flags=re.MULTILINE)
        label_end = m.start()
        jmp_search_target = codes[label_start:label_end]

    # scan JMPs
    jmps = re.findall(r'^([A-z_0-9]+:)?\s+((J[A-Z]*|SJ)\s+(.*?,\s([A-z_0-9]+)|([A-z_0-9]+)).*?)\s+;', jmp_search_target, flags=re.MULTILINE)
    # print(jmps)
    for j in jmps:
        if j[4] == '':
            graph.edge(l, j[5], xlabel=j[2])
        else:
            graph.edge(l, j[4], xlabel=j[2])

    # find fallthrough
    cs = jmp_search_target.splitlines()
    cs.reverse()
    for ics, lc in enumerate(cs):
        m = re.match(r'^\s+([A-Z]+)\s+', lc)
        if m is None:
            if ics == len(cs) - 1:
                m = re.match(r'^[A-z_0-9]+:\s+([A-Z]+)\s+', lc)
                if m is None:
                    break
            else:
                continue

        opcode = m.groups()[0]

        # print(re.match(r'(J[A-Z]+|RTI?|BRK)', opcode))
        if re.match(r'(J[A-Z]*|SJ|RTI?|BRK|DB)', opcode) is None and i < len(labels) - 1:
            graph.edge(l, labels[i + 1])
        if opcode == 'BRK':
            graph.node('exec SYSTEM_RESET from %s' % (l), shape='doubleoctagon')
            graph.edge(l, 'exec SYSTEM_RESET from %s' % (l))
        break # tail is found


    # find CAL/FCAL
    m = re.search(r'^([A-z_0-9]+:)?\s+([ASV]?CAL)\s+([A-z_0-9]+)', jmp_search_target, flags=re.MULTILINE)
    if m is not None:
        for cal in m.groups():
            opcode = m.groups()[1]
            oprand = m.groups()[2]
            # print(opcode, oprand)
            if opcode == 'VCAL':
                graph.node('CALL vcal_%d from %s' % (int(oprand), l), shape='doubleoctagon')
                graph.edge(l, 'CALL vcal_%d from %s' % (int(oprand), l), xlabel=opcode)
                graph.edge('CALL vcal_%d from %s' % (int(oprand), l), l, xlabel='RT')
            else:
                graph.edge(l, oprand, xlabel=opcode)
                graph.edge(oprand, l, xlabel='RT')

    # print(jr)
    # input()

print('rendering...')
graph.render('output')
# graph.view()

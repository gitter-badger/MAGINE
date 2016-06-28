import networkx as nx
import numpy as np
from py2cytoscape.data.cyrest_client import CyRestClient
from py2cytoscape.data.style import StyleUtil
from py2cytoscape.data.util_network import NetworkUtil as util

from cytoscape_mod_layout import LayoutClient


class RenderModel:
    def __init__(self, graph):
        self.graph = graph
        self.cy = CyRestClient()
        self.cy.session.delete()
        self.cy.layout = LayoutClient()
        self.style = None
        self.edge_name2id = None
        self.node_name2id = None
        self.g_cy = None
        self.view1 = None
        for n, i in enumerate(self.graph.edges()):
            self.graph[i[0]][i[1]]['name'] = str(i[0]) + ',' + str(i[1])

        self.g_cy = self.cy.network.create_from_networkx(self.graph)
        view_id_list = self.g_cy.get_views()
        self.view1 = self.g_cy.get_view(view_id_list[0], format='view')

        # Switch current visual style to a simple one...
        self.style = self.cy.style.create('Directed')
        options = {'NODE_LABEL_FONT_SIZE': 14,
                   'EDGE_WIDTH': 2,
                   'NETWORK_HEIGHT': '800',
                   'NETWORK_WIDTH': '800',
                   }
        self.style.update_defaults(options)
        # self.style = self.cy.style.create('Marquee')
        self.cy.layout.update(name="attributes-layout", parameters='color')
        self.cy.layout.apply(name="attributes-layout", network=self.g_cy)

        self.node_name2id = util.name2suid(self.g_cy, 'node')
        self.edge_name2id = util.name2suid(self.g_cy, 'edge')

        self.print_options()

    def print_options(self):
        node_vps = self.cy.style.vps.get_node_visual_props()
        for i in node_vps:
            print(i)
        edge_vps = self.cy.style.vps.get_edge_visual_props()
        for i in edge_vps:
            print(i)
        network_vps = self.cy.style.vps.get_network_visual_props()
        for i in network_vps:
            print(i)

    def visualize(self, list_of_time):

        node_label_values = {self.node_name2id[i[0]]: i[1]['label'] for i in self.graph.nodes(data=True)}
        node_color_values = {self.node_name2id[i[0]]: i[1]['color'] for i in self.graph.nodes(data=True)}
        edge_color_values = {}
        for i in self.edge_name2id:
            edge_color_values[self.edge_name2id[i]] = 'gray'
        edge_width_values = {}
        for i in self.graph.edges(data=True):
            edge_width_values[self.edge_name2id[str(i[0]) + ',' + str(i[1])]] = i[2]['weight']
        simple_slope = StyleUtil.create_slope(min=min(edge_width_values.values()),
                                              max=max(edge_width_values.values()),
                                              values=(1, 10))
        self.style.create_continuous_mapping(column='weight', col_type='Double', vp='EDGE_WIDTH', points=simple_slope)

        for j in list_of_time:
            size = np.array([self.graph.node[n][j] for n in self.graph.nodes()])
            simple_slope = StyleUtil.create_slope(min=size.min(), max=size.max(), values=(10, 60))
            self.style.create_continuous_mapping(column=j, col_type='Double', vp='NODE_SIZE', points=simple_slope)
            self.cy.style.apply(style=self.style, network=self.g_cy)
            self.view1.update_network_view(visual_property='NETWORK_SCALE_FACTOR', value='.9')
            # self.view1.update_network_view(visual_property='NETWORK_HEIGHT', value='800')
            # self.view1.update_network_view(visual_property='NETWORK_WIDTH', value='800')
            self.view1.update_network_view(visual_property='NETWORK_BACKGROUND_PAINT', value='white')
            self.view1.update_node_views(visual_property='NODE_LABEL', values=node_label_values)
            self.view1.update_node_views(visual_property='NODE_LABEL_COLOR', values=node_label_values)
            self.view1.update_node_views(visual_property='NODE_FILL_COLOR', values=node_color_values)
            self.view1.update_node_views(visual_property='NODE_BORDER_PAINT', values=node_color_values)
            self.view1.update_edge_views(visual_property='EDGE_LABEL_COLOR', values=edge_color_values)
            self.view1.update_edge_views(visual_property='EDGE_STROKE_UNSELECTED_PAINT', values=edge_color_values)
            self.view1.update_edge_views(visual_property='EDGE_SOURCE_ARROW_UNSELECTED_PAINT', values=edge_color_values)
            self.view1.update_edge_views(visual_property='EDGE_TARGET_ARROW_UNSELECTED_PAINT', values=edge_color_values)
            network_pdf = self.g_cy.get_svg()
            with open('{0}.svg'.format(j), 'wb') as f:
                f.write(network_pdf)
                f.close()
            network_pdf = self.g_cy.get_pdf()
            with open('{0}.pdf'.format(j), 'wb') as f:
                f.write(network_pdf)
                f.close()


if __name__ == '__main__':
    ddn = nx.nx.read_graphml('t_1_2_colored_enrichment.graphml')
    rm = RenderModel(ddn)
    rm.visualize(['time_0', 'time_1'])

import json
import unittest
from xml.etree import ElementTree as ET
from cdvector.model import Document, Shape, History

class ModelTests(unittest.TestCase):
    def test_save_roundtrip_all_shapes(self):
        doc=Document(shapes=[Shape('rect',[[4,5],[1,2]]),Shape('ellipse',[[0,0],[10,20]]),Shape('line',[[2,3],[8,9]]),Shape('bezier',[[0,0],[10,0],[10,10],[20,10]]),Shape('text',[[10,20]],text='Álefe & <vetor>')])
        self.assertEqual(Document.loads(doc.dumps()),doc)
        svg=ET.fromstring(doc.svg())
        self.assertEqual(len(svg),5)
        self.assertEqual(svg[-1].text,'Álefe & <vetor>')
        self.assertEqual(svg[0].get('width'),'3')
    def test_bezier_endpoints_and_midpoint(self):
        s=Shape('bezier',[[0,0],[0,10],[10,10],[10,0]])
        pts=s.samples(2)
        self.assertEqual(pts,[[0,0],[5,7.5],[10,0]])
    def test_history_restores_independent_state(self):
        h=History();d=Document();h.record(d);d.shapes.append(Shape('line',[[0,0],[10,10]]))
        d=h.undo(d);self.assertEqual(len(d.shapes),0)
        d=h.redo(d);self.assertEqual(len(d.shapes),1)
        h.record(d);d.shapes[0].move(12,8);d=h.undo(d)
        self.assertEqual(d.shapes[0].points,[[0,0],[10,10]])
    def test_rejects_invalid_geometry_and_colors(self):
        data=json.loads(Document(shapes=[Shape('rect',[[0,0],[2,2]])]).dumps())
        for key,val in [('points',[[float('nan'),0],[2,2]]),('fill','bad'),('width',-1),('kind','script')]:
            copy=json.loads(json.dumps(data));copy['shapes'][0][key]=val
            with self.assertRaises((ValueError,TypeError)):Document.loads(json.dumps(copy))

if __name__=='__main__':unittest.main()

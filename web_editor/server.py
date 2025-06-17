from flask import Flask, request, jsonify
import numpy as np

app = Flask(__name__)

@app.route('/cg', methods=['POST'])
def cg():
    data = request.get_json(force=True)
    shapes = data.get('shapes', [])
    area_total = 0.0
    cx_total = 0.0
    cy_total = 0.0
    for s in shapes:
        t = s.get('type')
        x = float(s.get('x', 0))
        y = float(s.get('y', 0))
        w = float(s.get('w', 0))
        h = float(s.get('h', 0))
        if t == 'rect':
            area = w * h
            cx = x + w/2
            cy = y + h/2
        elif t == 'tri':
            area = w * h / 2
            cx = x + w/3
            cy = y + h/3
        elif t == 'circ':
            area = np.pi * (w/2)**2
            cx = x
            cy = y
        else:
            continue
        area_total += area
        cx_total += cx * area
        cy_total += cy * area
    if area_total == 0:
        return jsonify({'error': 'area cero'}), 400
    return jsonify({'cg_x': cx_total/area_total, 'cg_y': cy_total/area_total})

if __name__ == '__main__':
    app.run(debug=True)

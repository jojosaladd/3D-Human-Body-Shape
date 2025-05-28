import sys
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtWidgets import QOpenGLWidget
from reshaper import Reshaper

import utils
import numpy as np

class PyQtOpenGL (QOpenGLWidget):
    def __init__(self, parent=None, ui=None):
        super().__init__(parent)
            # models for shape representing
        self.body = Reshaper(label="female")
        self.flag_ = 0
        self.ui = ui
        self.vertices = self.body.mean_vertex
        self.normals = self.body.normals
        self.facets = self.body.facets
        if np.max(self.facets) >= len(self.vertices):
            print("⚠️ Converting 1-based facets to 0-based indexing.")
            self.facets -= 1
        self.input_data = np.zeros((utils.M_NUM, 1))

        print("max facet index:", np.max(self.facets))
        print("vertices shape:", self.vertices.shape)
        print("normals shape:", self.normals.shape)
        print("facets shape:", self.facets.shape)
        print("max facet index:", np.max(self.facets))

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

        # Lighting setup
        glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 5.0, 1.0])  # Light in front of model
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])  # Soft base light

        # Material / color settings
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glColor3f(0.9, 0.9, 0.9)  # Set object color

        # Backface culling
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)  # Try GL_CCW first (CCW = counter-clockwise winding)

        # Background color
        glClearColor(0.2, 0.2, 0.2, 1.0)

    def resizeGL (self, w, h):
        glViewport(0, 0, w, h)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        # Maintain original 400:500 aspect (0.8)
        target_aspect = 400 / 500  # = 0.8
        current_aspect = w / h if h else 1

        if current_aspect > target_aspect:
            # Window is too wide — extend horizontal field of view
            gluPerspective(45.0, current_aspect, 1.0, 100.0)
        else:
            # Window is too tall or just right — use target aspect
            gluPerspective(45.0, target_aspect, 1.0, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -2.5)
        # Default orientation tweak
        glRotatef(180, 1.0, 0.0, 0.0)  # flip to front
        glRotatef(90, 1.0, 0.0, 0.0)   # lay upright


        glBegin(GL_TRIANGLES)
        for face in self.facets:
            for idx in face:
                if 0 <= idx < len(self.vertices):
                    base = idx * 3
                    if base + 2 < len(self.normals):
                        glNormal3f(
                            self.normals[base],
                            self.normals[base + 1],
                            self.normals[base + 2]
                        )
                    glVertex3f(*self.vertices[idx])
        glEnd()

    def save(self):
        # Save as 1-based facets (OBJ format expects that)
        utils.save_obj("result.obj", self.vertices, self.facets + 1)
        
        # Calculate measurements
        output = np.array(utils.calc_measure(self.body.cp, self.vertices, self.facets))
        
        for i in range(utils.M_NUM):
            print("%s: %f" % (utils.M_STR[i], output[i, 0]))

    def ok(self):
        def get_val(widget):
            try:
                val = widget.toPlainText()
                return float(val) if val else np.nan
            except ValueError:
                return np.nan

        # Your used indices in M_STR
        used_indices = {
            0: get_val(self.ui.weightEdit),
            1: get_val(self.ui.heightEidt),
            3: get_val(self.ui.chestEdit),
            10: get_val(self.ui.waistEdit),
            11: get_val(self.ui.hipEdit),
            7: get_val(self.ui.inseamEdit)
        }

        # Create input data array of shape (M_NUM, 1) with np.nan
        data = np.full((utils.M_NUM, 1), np.nan)
        for i, val in used_indices.items():
            data[i, 0] = val

        # Create mask for known inputs
        mask = ~np.isnan(data)

        # Normalize only the known entries
        norm_data = data.copy()
        for i in range(utils.M_NUM):
            if mask[i, 0]:
                norm_data[i, 0] -= self.body.mean_measure[i, 0]
                norm_data[i, 0] /= self.body.std_measure[i, 0]

        # Predict with imputation
        self.input_data = self.body.get_predict(mask, norm_data)

        # Update shape
        self.update()

        # For debug: print updated measurements
        updated_measure = self.body.mean_measure + self.input_data * self.body.std_measure
        for i in range(utils.M_NUM):
            print(f"{utils.M_STR[i]}: {updated_measure[i, 0]:.2f}")

    ##this works great! 
    def update(self):
        # Update body shape from predicted data
        self.vertices, self.normals, self.facets = self.body.mapping(self.input_data, self.flag_)

        # Ensure float32 type for OpenGL compatibility
        self.vertices = self.vertices.astype('float32')
        self.normals = self.normals.astype('float32')

        # Fix indexing if needed
        if np.max(self.facets) >= len(self.vertices):
            print("⚠️ Converting 1-based facets to 0-based indexing.")
            self.facets -= 1

        self.repaint()  # Triggers paintGL()

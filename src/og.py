import sys
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent, QWheelEvent

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
        self.input_data = np.zeros((utils.M_NUM, 1))
        
        self.facets -= 1
        
        print("OG: max facet index:", np.max(self.facets))
        print("OG: vertices shape:", self.vertices.shape)
        print("OG: normals shape:", self.normals.shape)
        print("OG: facets shape:", self.facets.shape)
        print("OG: max facet index:", np.max(self.facets))

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)


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
        # Step 1: Clear the screen
        glClearColor(0.2, 0.2, 0.2, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Step 2: Set up the modelview matrix
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        
        glTranslatef(0.0, 0.0, -2.5)
        glRotatef(180, 1.0, 0.0, 0.0)  # flip to front
        glRotatef(90, 1.0, 0.0, 0.0)   # lay upright
        glRotatef(20, 0.0, 0.0, 1.0)  # flip to front


        # Step 3: Enable and reconfigure lighting (after transforms!)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)

        #glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 5.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        #glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])

        #glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 10.0)  # smoother highlight

        # Step 4: Material color
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glColor3f(0.9, 0.9, 0.9)

        # # Step 5: Backface culling
        # glEnable(GL_CULL_FACE)
        # glCullFace(GL_BACK)
        #glFrontFace(GL_CW)

       # glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, 1)  # helps a lot during debugging


        # for face in range (0,12500):
        glBegin(GL_TRIANGLES)

        for face in self.facets:
            for idx in face:
                if 0 <= idx < len(self.vertices):
                    base = idx * 3
                    if base + 2 < len(self.normals):
                        # glNormal3f(0.0, 0.0, 1.0)  # fake normal pointing forward
                        # glVertex3f(*self.vertices[idx])
                        # print("Sample normals:")
                        # print(self.normals[0:9])  # first 3 normals
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

        # Get user input
        weight = get_val(self.ui.weightEdit)     # index 0
        height = get_val(self.ui.heightEdit)     # index 1
        chest = get_val(self.ui.chestEdit)       # index 3
        waist = get_val(self.ui.waistEdit)       # index 10
        hip = get_val(self.ui.hipEdit)           # index 11
        inseam = get_val(self.ui.inseamEdit)     # index 7

        
        # # Initialize data as nan
        data = np.full((utils.M_NUM, 1), np.nan)
        # print("DATA:",data)
        # # Apply the proper transformations (based on your earlier example)
        if not np.isnan(weight):
            data[0, 0] = weight ** (1.0 / 3.0) * 1000   # cube root × 1000
        if not np.isnan(height):
            data[1, 0] = height * 10                  # cm → scale ×10
        if not np.isnan(chest):
            data[3, 0] = chest  * 10
        if not np.isnan(inseam):
            data[7, 0] = inseam * 10
        if not np.isnan(waist):
            data[10, 0] = waist * 10
        if not np.isnan(hip):
            data[11, 0] = hip * 10

        #print("DATA:",data)
        #print("Mean weight (raw):", self.body.mean_measure[0, 0]) 4092
        #print("Mean height (raw):", self.body.mean_measure[1, 0]) 1631

        # # Create mask for known inputs
        mask = np.zeros((utils.M_NUM, 1), dtype=bool)

        for i in range(0, data.shape[0]):
             if not np.isnan(data[i, 0]): ##HERE i wanna make sure only areas with valid input(not NaN goes in but right now all values go in. )
               # print("HI? i is", i)
                data[i, 0] -= self.body.mean_measure[i, 0]
                data[i, 0] /= self.body.std_measure[i, 0]
                mask[i, 0] = 1
            

        # # Predict missing values using imputation
        self.input_data = self.body.get_predict(mask, data)
        self.updatep()

        # print("INPUT DATA?", self.input_data)
        # # Trigger update (if you define updateModel or just call self.update())

        # # Print predicted full-body measurements (de-normalized)
        updated_measure = self.body.mean_measure + self.input_data * self.body.std_measure
        # print("body_mean:", self.body.mean_measure)
        # print("updated measure:", updated_measure)

        ## here, i wanna set values (value[i, 0] / 10)) and  / 3.0 * 100.0))

    def updatep(self):
        # Update body shape from predicted data
        self.vertices, self.normals, self.facets = self.body.mapping(self.input_data, self.flag_)

        # Ensure float32 type for OpenGL compatibility
        self.vertices = self.vertices.astype('float32')
        self.normals = self.normals.astype('float32')
        self.normals *= -1.0

        self.facets += 1
        print("vertices shape:", self.vertices.shape)
        print("normals shape:", self.normals.shape)
        print("facets shape:", self.facets.shape)
        print("max facet index:", np.max(self.facets))
        print("len(vertices):", len(self.vertices))
        print("len(normals):", len(self.normals))

        # # Fix indexing if needed
        # if np.max(self.facets) >= len(self.vertices):
        #     print("⚠️ Converting 1-based facets to 0-based indexing.")
        #     self.facets -= 1
        #self.initializeGL()
        #self.makeCurrent()
        self.repaint()  # Triggers paintGL() ## probelm -> no lighting for the new model

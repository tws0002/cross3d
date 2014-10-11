##
#   :namespace  blur3d.api.maya.mayascene
#
#   :remarks    The MayaScene class will define all the operations for Maya scene interaction.
#				DEVELOPER NOTE: Native Objects should always be OpenMaya.MObject's not maya.cmds
#				objects.
#   
#   :author     mikeh@blur.com
#   :author     Blur Studio
#   :date       09/11/14
#

import re
from collections import OrderedDict
import collections as _collections
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaUI as omUI
import maya.OpenMayaAnim as oma

from blur3d import pendingdeprecation, constants
from blur3d.api.abstract.abstractscene import AbstractScene
from blurdev.enum import enum
from blurdev import debug
from blur3d import api
from blur3d.constants import ObjectType

class MayaScene(AbstractScene):
	# Create dicts used to map framerates to maya's time units
	_timeUnitToFPS = OrderedDict()
	for k, v in (('game', 15), ('film', 24), ('pal', 25), ('ntsc', 30), 
				('show', 48), ('palf', 50), ('ntscf', 60), ('millisec', 1000), 
				('sec', 1), ('min', 1/60.0), ('hour', 1/3600.0)):
		_timeUnitToFPS.update({k: v})
	for val in (2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 40, 75, 80, 100, 120, 150, 
				200, 240, 250, 300, 375, 400, 500, 600, 750, 1200, 2000, 3000, 6000):
		_timeUnitToFPS.update({'{}fps'.format(val): val})
	_timeUnitToConst = dict([(v, i) for i, v in _timeUnitToFPS.iteritems()])
	# This is used because OpenMaya.MTime doesnt't default to the current fps setting
	_fpsToMTime = OrderedDict()
	_fpsToMTime.update({'hour': om.MTime.kHours})
	_fpsToMTime.update({'min': om.MTime.kMinutes})
	_fpsToMTime.update({'sec': om.MTime.kSeconds}) # 1 fps
	_fpsToMTime.update({'2fps': om.MTime.k2FPS})
	_fpsToMTime.update({'3fps': om.MTime.k3FPS})
	_fpsToMTime.update({'4fps': om.MTime.k4FPS})
	_fpsToMTime.update({'5fps': om.MTime.k5FPS})
	_fpsToMTime.update({'6fps': om.MTime.k6FPS})
	_fpsToMTime.update({'8fps': om.MTime.k8FPS})
	_fpsToMTime.update({'10fps': om.MTime.k10FPS})
	_fpsToMTime.update({'12fps': om.MTime.k12FPS})
	_fpsToMTime.update({'game': om.MTime.kGames}) # 15 FPS
	_fpsToMTime.update({'16fps': om.MTime.k16FPS})
	_fpsToMTime.update({'20fps': om.MTime.k20FPS})
	_fpsToMTime.update({'film': om.MTime.kFilm}) # 24 fps
	_fpsToMTime.update({'pal': om.MTime.kPALFrame}) # 25 fps
	_fpsToMTime.update({'ntsc': om.MTime.kNTSCFrame}) # 30 fps
	_fpsToMTime.update({'40fps': om.MTime.k40FPS})
	_fpsToMTime.update({'show': om.MTime.kShowScan}) # 48 fps
	_fpsToMTime.update({'plaf': om.MTime.kPALField}) # # 50 fps
	_fpsToMTime.update({'ntscf': om.MTime.kNTSCField}) # 60 fps
	_fpsToMTime.update({'75fps': om.MTime.k75FPS})
	_fpsToMTime.update({'50fps': om.MTime.k80FPS})
	_fpsToMTime.update({'100fps': om.MTime.k100FPS})
	_fpsToMTime.update({'120fps': om.MTime.k120FPS})
	_fpsToMTime.update({'125fps': om.MTime.k125FPS})
	_fpsToMTime.update({'150fps': om.MTime.k150FPS})
	_fpsToMTime.update({'200fps': om.MTime.k200FPS})
	_fpsToMTime.update({'240fps': om.MTime.k240FPS})
	_fpsToMTime.update({'250fps': om.MTime.k250FPS})
	_fpsToMTime.update({'300fps': om.MTime.k300FPS})
	_fpsToMTime.update({'375fps': om.MTime.k375FPS})
	_fpsToMTime.update({'400fps': om.MTime.k400FPS})
	_fpsToMTime.update({'500fps': om.MTime.k500FPS})
	_fpsToMTime.update({'600fps': om.MTime.k600FPS})
	_fpsToMTime.update({'750fps': om.MTime.k750FPS})
	_fpsToMTime.update({'millisec': om.MTime.kMilliseconds}) # 1000 fps
	_fpsToMTime.update({'1200fps': om.MTime.k1200FPS})
	_fpsToMTime.update({'1500fps': om.MTime.k1500FPS})
	_fpsToMTime.update({'2000fps': om.MTime.k2000FPS})
	_fpsToMTime.update({'3000fps': om.MTime.k3000FPS})
	_fpsToMTime.update({'6000fps': om.MTime.k6000FPS})
#	_fpsToMTime.update({'last': om.MTime.kLast}) # Last value, used for counting
#	_fpsToMTime.update({'invalid': om.MTime.kInvalid}) # Invalid Value
	
	
	#--------------------------------------------------------------------------------
	#							Making OpenMaya pythonic
	#--------------------------------------------------------------------------------
	@classmethod
	def _currentTimeUnit(cls):
		""" Returns the current time unit name. See MayaScene._timeUnitToFPS to map this value
		to real world fps.
		:return: The name of the current fps
		"""
		return cmds.currentUnit(q=True, time=True)
	
	@classmethod
	def _createMTime(cls, value, unit=None):
		""" Constructs a OpenMaya.MTime with the provided value. If unit is None(its default)
		unit is set to the current unit setting in maya.
		:param value: The time value.
		:param unit: The time unit int value. See MayaScene._fpsToMTime for valid values. Defaults to None.
		:return: OpenMaya.MTime
		"""
		if unit == None:
			unit = cls._currentTimeUnit()
		return MTime(value, cls._fpsToMTime[unit])
	
	@classmethod
	def _selectionIter(cls):
		""" A Maya Helper that returns a iterator of maya objects currently
		selected.
		"""
		# Create object named selection and type - SelectionList
		selection = om.MSelectionList()
		# Fill variable "selection" with list of selected objects
		om.MGlobal.getActiveSelectionList(selection)
		# Create iterator through list of selected object
		selection_iter = om.MItSelectionList(selection)
		# Loop though iterator objects
		while not selection_iter.isDone():
			obj = om.MObject()
			selection_iter.getDependNode(obj)
			yield obj
			selection_iter.next()
	
	@classmethod
	def _objectsOfMTypeIter(cls, objectType):
		""" Maya Helper that returns a iterator of maya objects filtered by objectType.
		:param objectType: A enum value used to identify objects.
		.. seeAlso.. SceneObject._abstractToNativeObjectType
		"""
		if not isinstance(objectType, (tuple, list)):
			objectType = [objectType]
		for oType in objectType:
			# Create iterator traverse all camera nodes
			oIter = om.MItDependencyNodes(oType)
			# Loop though iterator objects
			while not oIter.isDone():
				# oIter.thisNode() points to current MObject in iterator
				yield oIter.thisNode()
				oIter.next()

	#--------------------------------------------------------------------------------
	#							blur3d private methods
	#--------------------------------------------------------------------------------

	def _createNativeCamera(self, name='Camera', type='Standard', target=None):
		""" Implements the AbstractScene._createNativeCamera method to return a new Studiomax camera
			:param name: <str>
			:return: <variant> nativeCamera || None
		"""
		if type == 'V-Ray':
			debug.debugObject(self._createNativeCamera, 'V-Ray cameras are not supported currently')
			return None
		else:
			if target != None:
				debug.debugObject(self._createNativeCamera, 'Target not supported currently.')
			tform, shape = cmds.camera()
			nativeCamera = api.SceneWrapper._asMOBject(shape)
		cmds.rename(tform, name)
		return nativeCamera

	def _findNativeObject(self, name='', uniqueId=0):
		""" Looks up a native object based on the inputed name or uniqueId. If name is provided
		it will find the object by the name, if uniqueId is provided it will look up the item by
		uniqueId.
		:param name: Name of the object. Defaults to a empty string.
		:param uniqueId: Unique ID of the object. Defaults to 0
		:return: nativeObject || None
		"""
		name = unicode(name)
		output = None
		found = False
		if name:
			sel = om.MSelectionList()
			sel.add(name)
			obj = om.MObject()
			sel.getDependNode(0, obj)
			if not obj.isNull():
				output = obj
				found = True
		if not found and uniqueId:
			debug.debugObject(self._findNativeObject, 'uniqueId not implemented yet.')
		return output

	def _fromNativeValue(self, nativeValue):
		""" Converts the inputed value from a native value from whatever application we're in
			:param nativeValue: <variant>
			:return:<variant>
		"""
		# by default, we assume all conversions have already occurred
		# Re-implented to shut-up the abstractmethod warning
		return nativeValue

	def _nativeObjects(self, getsFromSelection=False, wildcard='', objectType=0):
		""" Implements the AbstractScene._nativeObjects method to return the native objects from the scene
			:return: list [<Py3dsMax.mxs.Object> nativeObject, ..]
		"""
		if wildcard:
			# Maya uses pipes as seperators, so escape them so they are not treated as or's
			expression = re.sub(r'(?<!\\)\|', r'\|', wildcard)
			# This will replace any "*" into ".+" therefore converting basic star based wildcards into a regular expression.
			expression = re.sub(r'(?<!\\)\*', r'.*', expression)
			if not expression[-1] == '$':
				expression += '$'
		else:
			# No wildcard provided, match everything
			expression = '.*'
#		print expression
		regex = re.compile(expression, flags=re.I)
		if getsFromSelection:
			objects = self._selectionIter()
			if objectType != 0 or wildcard:
				ret = []
				for obj in objects:
					typeCheck = api.SceneObject._typeOfNativeObject(obj) & objectType == objectType
					wildcardCheck = regex.match(api.SceneObject._mObjName(obj))
#					print api.SceneObject._typeOfNativeObject(obj) & objectType,  api.SceneObject._typeOfNativeObject(obj), objectType, '----', typeCheck, wildcardCheck, api.SceneObject._mObjName(obj)
					if typeCheck and wildcardCheck:
						ret.append(obj)
				objects = ret
		else:
			if objectType == 0:
				# If a type was not provided, use the Generic type aka OpenMaya.MFn.kDagNode
				objectType = ObjectType.Generic
			# Get a list of objects by type from Maya
			mType = api.SceneObject._abstractToNativeObjectType[objectType]
			objects = self._objectsOfMTypeIter(mType)
			# If a wildcard was provided, filter results that don't match from the type objects
			if wildcard:
				ret = []
				for obj in objects:
					if regex.match(api.SceneObject._mObjName(obj)):
						ret.append(obj)
				objects = ret
		return objects

	def _nativeRootObject(self):
		""" Implements the AbstractScene._nativeRootObject to return the native root object of the scene
			:return: <Py3dsMax.mxs.Object> nativeObject || None
		"""
		for node in self._objectsOfMTypeIter(om.MFn.kWorld):
			# There should only be a single world node
			return node
		return None

	def _objects(self, getsFromSelection=False, wildcard='', type=0):
		""" Returns a list of all the objects in the scene wrapped as api objects
			:param: getsFromSelection <bool>
			:param: wildcard <string>
			:param: type <blur3d.constants.ObjectType>
			:return: <list> [ <blur3d.api.Variant>, .. ]
		"""
		from blur3d.api import SceneObject
		return [SceneObject(self, obj) for obj in self._nativeObjects(getsFromSelection, wildcard, type) if obj.apiType() != om.MFn.kWorld]

	def _nativeRefresh(self):
		""" Refreshes the contents of the current scene
			:sa: setUpdatesEnabled, update
			:return: <bool> success
		"""
		return self.viewport().nativePointer().refresh(True, True)

	def _removeNativeObjects(self, nativeObjects):
		""" Removes the inputed objects from the scene
			:param nativeObjects:	<list> [ <variant> nativeObject, .. ]
			:return: <bool> success
		"""
		objs = []
		for obj in nativeObjects:
			if not isinstance(obj, basestring):
				obj = api.SceneWrapper._mObjName(obj, True)
			objs.append(obj)
		cmds.delete(*objs)
		return True

	def _setNativeSelection(self, selection):
		""" Select the inputed native objects in the scene
			:param selection: <list> [ <PySoftimage.xsi.Object> nativeObject, .. ] || MSelectionList || str || unicode
			:return: <bool> success
		"""
		if isinstance(selection, basestring):
			try:
				om.MGlobal.selectByName(selection)
			except RuntimeError, e:
				if e.message.find('kNotFound') != -1:
					# No objects were selected
					return False
				else:
					# Something is broken. Investigate as needed
					raise
			finally:
				return True
		else:
			if not isinstance(selection, om.MSelectionList):
				# Build a selection List
				tempList = om.MSelectionList()
				for obj in selection:
					# Passing the object directly doesnt seem to work
					dagPath = om.MDagPath.getAPathTo(obj)
					tempList.add(dagPath)
				selection = tempList
			om.MGlobal.setActiveSelectionList(selection)
		return True

	#--------------------------------------------------------------------------------
	#							blur3d public methods
	#--------------------------------------------------------------------------------

	def animationFPS(self):
		""" Return the current frames per second rate.
			:return: float
		"""
		base = self._currentTimeUnit()
		return float(self._timeUnitToFPS[base])

	def setAnimationFPS(self, fps, changeType=constants.FPSChangeType.Seconds, callback=None):
		""" Updates the scene's fps to the provided value and scales existing keys as specified.
		StudioMax Note: If you have any code that you need to run after changing the fps and plan to use it in
			3dsMax you will need to pass that code into the callback argument.
		Maya Note: Maya only supports specific fps settings. If you provide it with a value it doesn't understand,
			it will be set to the closest matching value. See MayaScene._timeUnitToFPS for valid values.
		:param fps: The FPS value to set.
		:param changeType: <constants.FPSChangeType> Defaults to constants.FPSChangeType.Frames
		:param callback: <funciton> Code called after the fps is changed.
		:return: bool success
		"""
		# Maya doesn't appear to allow you to set the fps to a specific value,
		# so we attempt to find a exact match in our _fpsToTimeUnit dictonary
		name = self._fpsToTimeUnit.get(fps)
		if not name:
			# If there isn't a exact match, find the value closest to the requested fps.
			closest = min(self._fpsToTimeUnit, key=lambda x: abs(x - fps))
			name = self._fpsToTimeUnit[closest]
		# Only update the fps if the value is different
		if name != self._currentTimeUnit():
			# Only update animation if Seconds is specified
			updateAnimation = changeType == constants.FPSChangeType.Seconds
			cmds.currentUnit(time=name, updateAnimation=updateAnimation)
		if callback:
			callback()
		return True

	def animationRange(self):
		"""
			\remarks	implements AbstractScene.animationRange method to return the current animation start and end frames
			\return		<blur3d.api.FrameRange>
		"""
		playControl = oma.MAnimControl
		return api.FrameRange([int(playControl.minTime().value()), int(playControl.maxTime().value())])

	def setAnimationRange(self, animationRange, globalRange=None):
		""" Sets the current start and end frame for animation.
			:param animationRange: <tuple> ( <int> start, <int> end )
			:param globalRange: <tuple> ( <int> start, <int> end ). If not provided set the global range to animationRange
			:return: success
		"""
		if not globalRange:
			globalRange = animationRange
		playControl = oma.MAnimControl
		
		playControl.setAnimationStartEndTime(om.MTime(globalRange[0]), om.MTime(globalRange[1]))
		playControl.setMinMaxTime(om.MTime(animationRange[0]), om.MTime(animationRange[1]))
		return True

	def clearSelection(self):
		""" Clear the selection in the scene.
			:return: <bool> success
		"""
		om.MGlobal.clearSelectionList()
		return True

	@classmethod
	def currentFileName(cls):
		""" Implements AbstractScene.currentFileName method to return the current filename for the scene that is active in the application
			:return: The current File name as a string
		"""
		return cmds.file(query=True, sceneName=True)
	
	def renderSize(self):
		""" Return the render output size for the scene
			:return: <QSize>
		"""
		from PyQt4.QtCore import QSize
		width = cmds.getAttr('defaultResolution.width')
		height = cmds.getAttr('defaultResolution.height')
		return QSize(width, height)
	
	def setRenderSize(self, size):
		""" Set the render output size for the scene
			:param size: <QSize>
		"""
		from PyQt4.QtCore import QSize
		if isinstance(size, QSize):
			width = size.width()
			height = size.height()
		elif isinstance(size, list):
			if len(size) < 2:
				raise TypeError('You must provide a width and a height when setting the render size using a list')
			width = size[0]
			height = size[1]
		cmds.setAttr('defaultResolution.width', width)
		cmds.setAttr('defaultResolution.height', height)
		return True
	
	def setSelection(self, objects, additive=False):
		""" Selects the inputed objects in the scene
			:param objects: <list> [ <blur3d.api.SceneObject>, .. ]
			:return: <bool> success
		"""
		if isinstance(objects, basestring):
			return self._addToNativeSelection(objects) if additive else self._setNativeSelection(objects)
		elif isinstance(objects, _collections.Iterable):
			# Note: This is passing the transform object not the nativePointer
			nativeObjects = [obj._nativeTransform for obj in objects]
			return self._addToNativeSelection(nativeObjects) if additive else self._setNativeSelection(nativeObjects)
		raise TypeError('Argument 1 must be str or list of blur3d.api.SceneObjects')
	
	def viewports(self):
		""" Returns all the visible viewports
			:return: [<blur3d.api.SceneViewport>, ...]
		"""
		out = []
		for index in range(omUI.M3dView.numberOf3dViews()):
			out.append(api.SceneViewport(self, index))
		return out

# register the symbol
api.registerSymbol('Scene', MayaScene)
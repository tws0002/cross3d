##
#   \namespace  blur3d.api.classes.exceptions
#
#   \remarks    [desc::commented]
#   
#   \author     douglas@blur.com
#   \author     Blur Studio
#   \date       02/24/12
#

#--------------------------------------------------------------------------------

class Exceptions:

	class Blur3DException( Exception ):
		'''
			Raise exceptions specific to blur3d.
		'''
		pass
	
	class FPSChangeFailed(Blur3DException):
		"""
			Exception Raised if unable to change the FPS
		"""
		pass
		
	class OutputFailed(Blur3DException):
		"""
			Exception Raised if unable to change the FPS
		"""
		pass
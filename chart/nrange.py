import math


POINTS_PER_MAJOR = 1000

class NumericRange(object):
#==========================

  """
  Calculate spacing of major and minor grid points.
  
  Major spacing is selected to be either 1, 2, or 5, multipled by
  a power of ten; minor spacing is respectively 0.2, 0.5 or 1.0.

  Spacing is chosen so that around 10 major grid points span the
  interval.

  :param w: The width of the interval.
  :return: A tuple with (major, minor) spacing.
  """

  def __init__(self, start, end):
  #------------------------------
    width = end - start
    if   width < 0.0:
      width = -width
      start = end
      end = start + width
    elif width == 0.0: raise ValueError("Grid cannot have zero width")
    l = math.log10(width)
    f = math.floor(l)
    x = l - f     # Normalised between 0.0 and 1.0
    scale = math.pow(10.0, f)
    (self.major, self.minor) = ( ( 1*scale/10, 0.02*scale) if x < 0.15 # The '/10' appears to
                            else ( 2*scale/10, 0.05*scale) if x < 0.50 # minimise rounding errors
                            else ( 5*scale/10, 0.10*scale) if x < 0.85  
                            else (10*scale/10, 0.20*scale) )
    self.quanta = self.major/POINTS_PER_MAJOR
    self.start = self.major*math.floor(start/self.major)
    self.end = self.major*math.ceil(end/self.major)
    self.major_size = int(math.floor((self.end-self.start)/self.major + 0.5))

  def map(self, a, extra=0):
  #-------------------------
    q = self.quanta/float(math.pow(10, extra))
    return q*math.floor((a + q/2.0)/q)


if __name__ == '__main__':
#=========================

  r = NumericRange(3.035687, 30.47)
  r = NumericRange(0, 1806.6)

  print r.start, r.end, r.major, r.minor, r.quanta

  def test(a):
  #-----------
    print a, '==>', r.map(a)

  test(30.035667565)
  test(30.035671565)

  test(1806.6)

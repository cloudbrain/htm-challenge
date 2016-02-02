import platform
import sys

from setuptools import find_packages, setup


def findRequirements():
  """
  Read the requirements.txt file and parse into requirements for setup's
  install_requirements option.
  """
  return [
    line.strip()
    for line in open("requirements.txt").readlines()
    if not line.startswith("#")
  ]


depLinks = []
if "linux" in sys.platform and platform.linux_distribution()[0] == "CentOS":
  depLinks = [ "https://pypi.numenta.com/pypi/nupic",
               "https://pypi.numenta.com/pypi/nupic.bindings" ]

setup(name="brainsquared",
      version="0.0.1",
      description="HTM Challenge 2015 code",
      author="Marion Le Borgne, Pierre Karashchuk",
      url="https://github.com/CloudbrainLabs/htm-challenge",
      packages=find_packages(),
      install_requires=findRequirements(),
      dependency_links = depLinks, requires=['numpy']
      )

from conans import ConanFile, CMake, tools
import os
from io import StringIO


class SDL2TtfTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def imports(self):
        self.copy("*.dll", dst="bin", src="bin")
        self.copy("*.dylib", dst="bin", src="lib")
        self.copy("*.so*", dst="bin", src="lib")
        self.copy("*.ttf", dst="bin", src="")

    def test(self):
        if not tools.cross_building(self.settings):
            out = StringIO()
            os.chdir("bin")
            try:
                self.run(".%sexample" % os.sep, output=out)
            finally:
                print("**********\n%s***********" % str(out.getvalue()))
            assert "Couldn't find matching render driver" in str(out.getvalue()) or "No available video device" in str(out.getvalue()) or "Closing window" in str(out.getvalue())

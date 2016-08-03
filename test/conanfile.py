from conans import ConanFile
from conans import GCC, CMake
import os
from StringIO import StringIO

############### CONFIGURE THESE VALUES ##################
default_user = "lasote"
default_channel = "testing"
#########################################################

channel = os.getenv("CONAN_CHANNEL", default_channel)
username = os.getenv("CONAN_USERNAME", default_user)


class DefaultNameConan(ConanFile):
    name = "DefaultName"
    version = "0.1"
    settings = "os", "compiler", "build_type", "arch"
    requires = "SDL2_ttf/2.0.14@%s/%s" % (username, channel)
    generators = ["cmake"] # Generates conanbuildinfo.gcc with all deps information

    def build(self):
        cmake = CMake(self.settings)
        self.run('cmake %s %s' % (self.conanfile_directory, cmake.command_line))
        self.run("cmake --build . %s" % cmake.build_config)

    def imports(self):
        self.copy(pattern="*.dll", dst="bin", src="bin")
        self.copy(pattern="*.dylib", dst="bin", src="lib")
        self.copy(pattern="*.ttf", dst="bin", src="")

    def test(self):
        out = StringIO()
        self.run("cd bin && .%sexample || true" % (os.sep),  output=out)
        print("**********\n%s***********" % str(out.getvalue()))
        assert "No available video device" in str(out.getvalue()) or "Closing window" in str(out.getvalue())
        
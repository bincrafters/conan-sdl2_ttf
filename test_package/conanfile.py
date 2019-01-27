from conans import ConanFile, CMake, tools
import os


class SDL2TtfTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        cmake.definitions["FONT_PATH"] = os.path.join(os.path.dirname(os.path.realpath(__file__)), "OpenSans-Bold.ttf").replace("\\", "\\\\")
        cmake.configure()
        cmake.build()

    def imports(self):
        self.copy("*.dll", dst="bin", src="bin")
        self.copy("*.dylib", dst="bin", src="lib")
        self.copy("*.so*", dst="bin", src="lib")

    def test(self):
        if not tools.cross_building(self.settings):
            os.chdir("bin")
            self.run(".%stest_package" % os.sep)

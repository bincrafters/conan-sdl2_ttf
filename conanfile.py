from conans import ConanFile, tools, MSBuild, AutoToolsBuildEnvironment
import os
import os.path

class SDL2TtfConan(ConanFile):
    name = "sdl2_ttf"
    version = "2.0.14"
    folder = "SDL2_ttf-%s" % version
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = (
        "shared=True",
        "fPIC=True",
    )
    url = "http://github.com/elizagamedev/conan-sdl2_ttf"
    requires = "sdl2/2.0.8@bincrafters/stable"
    license = "MIT"

    def config_options(self):
        del self.settings.compiler.libcxx
        if self.settings.compiler == "Visual Studio":
            del self.options.shared
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.settings.compiler == "Visual Studio":
            self.options["sdl2"].shared = True

    def requirements(self):
        if self.settings.compiler != "Visual Studio":
            self.requires("freetype/2.9.0@bincrafters/stable")

    def source(self):
        tools.get("https://www.libsdl.org/projects/SDL_ttf/release/{}.tar.gz".format(self.folder))
        if self.settings.compiler == "Visual Studio":
            visualc = os.path.join(self.folder, "VisualC")
            tools.replace_in_file(os.path.join(visualc, "SDL_ttf.vcxproj"),
                                  "<AdditionalDependencies>",
                                  "<AdditionalDependencies>WinMM.lib;version.lib;Imm32.lib;")
            tools.replace_in_file(os.path.join(visualc, "glfont", "glfont.vcxproj"),
                                  "<AdditionalDependencies>",
                                  "<AdditionalDependencies>WinMM.lib;version.lib;Imm32.lib;")
            tools.replace_in_file(os.path.join(visualc, "showfont", "showfont.vcxproj"),
                                  "<AdditionalDependencies>",
                                  "<AdditionalDependencies>WinMM.lib;version.lib;Imm32.lib;")

    def build(self):
        if self.settings.compiler == "Visual Studio":
            self.build_with_vs()
        else:
            self.build_with_make()

    def build_with_vs(self):
        msbuild = MSBuild(self)
        msbuild.build(os.path.join(self.folder, "VisualC", "SDL_ttf.sln"),
                      platforms={"x86": "Win32",
                                 "x86_64": "x64"},
                      toolset=self.settings.compiler.toolset)

    def build_with_make(self):
        autotools = AutoToolsBuildEnvironment(self)
        sharedargs = (['--enable-shared', '--disable-static']
                      if self.options.shared else
                      ['--enable-static', '--disable-shared'])
        autotools.configure(configure_dir=self.folder, args=[
            "--with-freetype-exec-prefix=" + self.deps_cpp_info["freetype"].lib_paths[0]
        ] + sharedargs)

        old_str = '\nLIBS = '
        new_str = '\n# Removed by conan: LIBS = '
        tools.replace_in_file("Makefile", old_str, new_str)

        old_str = '\nLIBTOOL = '
        new_str = '\nLIBS = {}\nLIBTOOL = '.format(" ".join(["-l%s" % lib for lib in self.deps_cpp_info.libs])) # Trust conaaaan!
        tools.replace_in_file("Makefile", old_str, new_str)

        old_str = '\nSDL_CFLAGS ='
        new_str = '\n# Removed by conan: SDL_CFLAGS ='
        tools.replace_in_file("Makefile", old_str, new_str)

        old_str = '\nSDL_LIBS ='
        new_str = '\n# Removed by conan: SDL_LIBS ='
        tools.replace_in_file("Makefile", old_str, new_str)

        autotools.make()
        autotools.install()

    def package(self):
        if self.settings.compiler == "Visual Studio":
            self.copy(pattern="SDL_ttf.h", dst=os.path.join("include", "SDL2"), src=self.folder, keep_path=False)
            self.copy(pattern="*/SDL2_ttf.lib", dst="lib", keep_path=False)
            self.copy(pattern="*/SDL2_ttf.pdb", dst="lib", keep_path=False)
            self.copy(pattern="*/SDL2_ttf.dll", dst="bin", keep_path=False)
            self.copy(pattern="*/libfreetype*.dll", dst="bin", keep_path=False)
            self.copy(pattern="*/zlib*.dll", dst="bin", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join("include", "SDL2"))

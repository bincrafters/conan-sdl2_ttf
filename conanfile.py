from conans import ConanFile, tools, MSBuild, AutoToolsBuildEnvironment
import os
import os.path

class SDL2TtfConan(ConanFile):
    name = "sdl2_ttf"
    version = "2.0.14"
    description = "A TrueType font library for SDL2"
    topics = ("conan", "sdl2", "sdl2_ttf", "sdl", "sdl_ttf", "ttf", "font")
    url = "https://github.com/bincrafters/conan-sdl2_ttf"
    homepage = "https://www.libsdl.org/projects/SDL_ttf/"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "ZLIB"
    exports = "LICENSE.md"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": False,
    }

    _source_subfolder = "SDL2_ttf-{}".format(version)

    requires = (
        "freetype/2.9.0@bincrafters/stable",
        "sdl2/2.0.8@bincrafters/stable",
    )

    def config_options(self):
        del self.settings.compiler.libcxx
        if self.settings.compiler == "Visual Studio":
            del self.options.shared
        if self.settings.os == "Windows":
            del self.options.fPIC

    def source(self):
        tools.get("https://www.libsdl.org/projects/SDL_ttf/release/{}.tar.gz".format(
            self._source_subfolder))
        if self.settings.compiler == "Visual Studio":
            visualc = os.path.join(self._source_subfolder, "VisualC")

            projects = (
                os.path.join(visualc, "SDL_ttf.vcxproj"),
                os.path.join(visualc, "glfont", "glfont.vcxproj"),
                os.path.join(visualc, "showfont", "showfont.vcxproj"),
            )

            # Patch out dependency on packaged freetype
            tools.replace_in_file(projects[0], "external\\include;", "")
            tools.replace_in_file(projects[0], "external\\lib\\x86;", "")
            tools.replace_in_file(projects[0], "external\\lib\\x64;", "")
            tools.replace_in_file(projects[0], "libfreetype-6.lib;", "")

            # Patch in some missing libraries
            for project in projects:
                tools.replace_in_file(project,
                                      "<AdditionalDependencies>",
                                      "<AdditionalDependencies>WinMM.lib;version.lib;Imm32.lib;")
                if self.settings.build_type == "Debug":
                    tools.replace_in_file(project, "SDL2.lib", "SDL2d.lib", strict=False)
                    tools.replace_in_file(project, "SDL2main.lib", "SDL2maind.lib", strict=False)

    def build(self):
        if self.settings.compiler == "Visual Studio":
            self.build_with_vs()
        else:
            if self.settings.os == "Macos":
                with tools.environment_append({"DYLD_LIBRARY_PATH": self.deps_cpp_info["sdl2"].libdirs}):
                    self.build_with_make()
            else:
                self.build_with_make()

    def build_with_vs(self):
        msbuild = MSBuild(self)
        msbuild.build(os.path.join(self._source_subfolder, "VisualC", "SDL_ttf.sln"),
                      platforms={"x86": "Win32",
                                 "x86_64": "x64"},
                      toolset=self.settings.compiler.toolset)

    def build_with_make(self):
        autotools = AutoToolsBuildEnvironment(self)
        args = [
            "--with-freetype-prefix=" + self.deps_cpp_info["freetype"].rootpath,
            "--with-sdl-prefix=" + self.deps_cpp_info["sdl2"].rootpath,
        ]
        if self.options.shared:
            args.extend(['--enable-shared', '--disable-static'])
        else:
            args.extend(['--enable-static', '--disable-shared'])
        autotools.configure(configure_dir=self._source_subfolder, args=args)

        patches = (
            ('\nnoinst_PROGRAMS = ', '\n# Removed by conan: noinst_PROGRAMS = '),
            ('\nLIBS = ', '\n# Removed by conan: LIBS = '),
            ('\nLIBTOOL = ', '\nLIBS = {}\nLIBTOOL = '.format(" ".join(["-l%s" % lib for lib in self.deps_cpp_info.libs]))),
            ('\nSDL_CFLAGS =', '\n# Removed by conan: SDL_CFLAGS ='),
            ('\nSDL_LIBS =' , '\n# Removed by conan: SDL_LIBS ='),
        )

        for old_str, new_str in patches:
            tools.replace_in_file("Makefile", old_str, new_str)

        autotools.make()
        autotools.install()

    def package(self):
        if self.settings.compiler == "Visual Studio":
            self.copy(pattern="SDL_ttf.h",
                      dst=os.path.join("include", "SDL2"),
                      src=self._source_subfolder,
                      keep_path=False)
            self.copy(pattern="*{}SDL2_ttf.lib".format(os.sep), dst="lib", keep_path=False)
            self.copy(pattern="*{}SDL2_ttf.pdb".format(os.sep), dst="lib", keep_path=False)
            self.copy(pattern="*{}SDL2_ttf.dll".format(os.sep), dst="bin", keep_path=False)
            self.copy(pattern="*{}COPYING.txt".format(os.sep), dst="licenses", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.includedirs.append(os.path.join("include", "SDL2"))

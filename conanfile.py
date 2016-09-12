from conans import ConanFile
from conans.tools import download, unzip, replace_in_file, vcvars_command
import os
import shutil
from conans import CMake, ConfigureEnvironment
import platform

class SDL2TTfConan(ConanFile):
    name = "SDL2_ttf"
    version = "2.0.14"
    folder = "SDL2_ttf-%s" % version
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = '''shared=False
    fPIC=True'''
    generators = "cmake"
    url="http://github.com/lasote/conan-SDL2_ttf"
    requires = "SDL2/2.0.4@lasote/stable", "freetype/2.6.3@lasote/stable"
    license="MIT"

    def configure(self):
        # del self.settings.compiler.libcxx
        self.options["SDL2"].shared = self.options.shared


    def source(self):
        zip_name = "%s.tar.gz" % self.folder
        download("https://www.libsdl.org/projects/SDL_ttf/release/%s" % zip_name, zip_name)
        unzip(zip_name)

    def build(self):
        if self.settings.os == "Windows":
            self.build_with_vs()
        else:
            self.build_with_make()

    def build_with_vs(self):
        env = ConfigureEnvironment(self.deps_cpp_info, self.settings)

        libdirs="<AdditionalLibraryDirectories>"
        libdirs_ext="<AdditionalLibraryDirectories>$(LIB);"
        replace_in_file("%s\VisualC\SDL_ttf.vcxproj" % self.folder, libdirs, libdirs_ext)
        replace_in_file("%s\VisualC\SDL_ttf.vcxproj" % self.folder, "<AdditionalDependencies>", "<AdditionalDependencies>WinMM.lib;version.lib;Imm32.lib;")
        replace_in_file("%s\VisualC\glfont\glfont.vcxproj" % self.folder, "<Link>", "<Link>%s</AdditionalLibraryDirectories>" % libdirs_ext)
        replace_in_file("%s\VisualC\glfont\glfont.vcxproj" % self.folder, "<AdditionalDependencies>", "<AdditionalDependencies>WinMM.lib;version.lib;Imm32.lib;")
        replace_in_file("%s\VisualC\showfont\showfont.vcxproj" % self.folder, "<Link>", "<Link>%s</AdditionalLibraryDirectories>" % libdirs_ext)
        replace_in_file("%s\VisualC\showfont\showfont.vcxproj" % self.folder, "<AdditionalDependencies>", "<AdditionalDependencies>WinMM.lib;version.lib;Imm32.lib;")

        vcvars_cmd = vcvars_command(self.settings)
        cd_build = "cd %s\VisualC" % self.folder
        command = "%s && %s && %s && devenv SDL_ttf.sln /upgrade" % (vcvars_cmd, cd_build, env.command_line)
        self.output.warn(command)
        self.run(command)
        self.run("%s && %s && %s && msbuild SDL_ttf.sln" % (vcvars_cmd, cd_build, env.command_line))

    def build_with_make(self):

        env = ConfigureEnvironment(self.deps_cpp_info, self.settings)
        if self.options.fPIC:
            env_line = env.command_line.replace('CFLAGS="', 'CFLAGS="-fPIC ')
        else:
            env_line = env.command_line

        # env_line = env_line.replace('LIBS="', 'LIBS2="') # Rare error if LIBS is kept
        sdl2_config_path = os.path.join(self.deps_cpp_info["SDL2"].lib_paths[0], "sdl2-config")
        self.run("cd %s" % self.folder)
        self.run("chmod a+x %s/configure" % self.folder)
        self.run("chmod a+x %s" % sdl2_config_path)

        self.output.warn(env_line)
        if self.settings.os == "Macos": # Fix rpath, we want empty rpaths, just pointing to lib file
            old_str = "-install_name \$rpath/"
            new_str = "-install_name "
            replace_in_file("%s/configure" % self.folder, old_str, new_str)
        if self.settings.os == "Linux":
            env_line = env_line.replace("-lbz2", "") # Configure fails because of double main declaration WTF

        freetype_location = self.deps_cpp_info["freetype"].lib_paths[0]
        shared = "--enable-shared=yes --enable-static=no" if self.options.shared else "--enable-shared=no --enable-static=yes"
        configure_command = 'cd %s && %s SDL2_CONFIG=%s ./configure --with-freetype-exec-prefix="%s" %s' % (self.folder, env_line, sdl2_config_path, freetype_location, shared)
        self.output.warn("Configure with: %s" % configure_command)
        self.run(configure_command)


        old_str = '\nLIBS = '
        new_str = '\n# Removed by conan: LIBS2 = '
        replace_in_file("%s/Makefile" % self.folder, old_str, new_str)

        old_str = '\nLIBTOOL = '
        new_str = '\nLIBS = %s \nLIBTOOL = ' % " ".join(["-l%s" % lib for lib in self.deps_cpp_info.libs]) # Trust conaaaan!
        replace_in_file("%s/Makefile" % self.folder, old_str, new_str)

        old_str = '\nSDL_CFLAGS ='
        new_str = '\n# Commented by conan: SDL_CFLAGS ='
        replace_in_file("%s/Makefile" % self.folder, old_str, new_str)

        old_str = '\nSDL_LIBS ='
        new_str = '\n# Commented by conan: SDL_LIBS ='
        replace_in_file("%s/Makefile" % self.folder, old_str, new_str)

        old_str = '\nCFLAGS ='
        new_str = '\n# Commented by conan: CFLAGS ='
        replace_in_file("%s/Makefile" % self.folder, old_str, new_str)

        old_str = '\n# Commented by conan: CFLAGS ='
        fpic = "-fPIC"  if self.options.fPIC else ""
        m32 = "-m32" if self.settings.arch == "x86" else ""
        debug = "-g" if self.settings.build_type == "Debug" else "-s -DNDEBUG"
        new_str = '\nCFLAGS =%s %s %s %s\n# Commented by conan: CFLAGS =' % (" ".join(self.deps_cpp_info.cflags), fpic, m32, debug)
        replace_in_file("%s/Makefile" % self.folder, old_str, new_str)


        self.output.warn(str(self.deps_cpp_info.libs))

        self.run("cd %s && %s make" % (self.folder, env_line))

    def package(self):
        """ Define your conan structure: headers, libs and data. After building your
            project, this method is called to create a defined structure:
        """
        self.copy(pattern="SDL_ttf.h", dst="include", src="%s" % self.folder, keep_path=False)
        self.copy(pattern="SDL_ttf.h", dst="include/SDL2", src="%s" % self.folder, keep_path=False)

        if self.settings.os == "Windows":
            self.copy(pattern="*.lib", dst="lib", src="%s" % self.folder, keep_path=False)
            #Don't copy VERSION.dll because it is also provided by Windows and causes a verification error
            self.copy(pattern="*_ttf.dll", dst="bin", src="%s" % self.folder, keep_path=False)
            self.copy(pattern="*6.dll", dst="bin", src="%s" % self.folder, keep_path=False)
            self.copy(pattern="*1.dll", dst="bin", src="%s" % self.folder, keep_path=False)
        # UNIX
        elif self.options.shared:
            self.copy(pattern="*.a", dst="lib", src="%s" % self.folder, keep_path=False)
            self.copy(pattern="*.a", dst="lib", src="%s" % self.folder, keep_path=False)
        else:
            self.copy(pattern="*.so*", dst="lib", src="%s" % self.folder, keep_path=False)
            self.copy(pattern="*.dylib*", dst="lib", src="%s" % self.folder, keep_path=False)

    def package_info(self):

        self.cpp_info.libs = ["SDL2_ttf"]

#!/usr/bin/env python
# coding: utf-8

import os
import pprint
from tests.common import TestCase
from tests.common import EXAMPLE_DATA_PATH
from clocwalk.libs.analyzer.gradle import find_keyword_block
from clocwalk.libs.analyzer.gradle import find_include_file
from clocwalk.libs.analyzer.gradle import start


class GradleTestCase(TestCase):

    def setUp(self):
        pass

    def test_find_dependencies_block(self):
        """

        :return:
        """
        content = """buildscript {
    apply from: rootProject.file("dependencies.gradle")
    repositories {
        google()
        maven { url "https://plugins.gradle.org/m2/" }
        jcenter()
    }
    dependencies {
        classpath deps.build.androidPlugin
        classpath deps.build.butterKnifePlugin
        classpath deps.build.kotlinPlugin
        classpath deps.build.kotlinAllOpen
        classpath deps.build.sqlDelightPlugin
        classpath deps.build.shadowJar
    }
    configurations.all {
        exclude group:"com.android.tools.build", module: "transform-api"
    }
}

allprojects {
    task allDeps(type: DependencyReportTask) {}
}

allprojects { project ->
    project.apply from: rootProject.file("dependencies.gradle")
    repositories {
        google()
        maven { url "https://plugins.gradle.org/m2/" }
        jcenter()
    }
    configurations.all {
        exclude group:"com.android.tools.build", module: "transform-api"
    }
}

apply plugin: "com.uber.okbuck"

subprojects { project ->
    afterEvaluate {
        if (project.plugins.hasPlugin("java")) {
            addCommonConfigurationForJavaModules(project)
        } else if (project.plugins.hasPlugin("com.android.application")
                || project.plugins.hasPlugin("com.android.library")) {
            addCommonConfigurationForAndroidModules(project)
        }

        project.tasks.withType(Test) { Test task ->
            task.jvmArgs << "-Djava.awt.headless=true"
        }
    }
}

def addCommonConfigurationForJavaModules(Project project) {
    project.sourceCompatibility = JavaVersion.VERSION_1_8
    project.targetCompatibility = JavaVersion.VERSION_1_8
}

def addCommonConfigurationForAndroidModules(Project project) {
    project.android {
        compileSdkVersion config.build.compileSdk
        buildToolsVersion config.build.buildTools

        defaultConfig {
            minSdkVersion config.build.minSdk
            targetSdkVersion config.build.targetSdk
            vectorDrawables.useSupportLibrary = true
            versionCode 1
            versionName "1.0"
        }

        compileOptions {
            sourceCompatibility JavaVersion.VERSION_1_8
            targetCompatibility JavaVersion.VERSION_1_8
        }

        lintOptions {
            lintConfig project.rootProject.file("lint.xml")
        }
    }

    def variants
    if (project.plugins.hasPlugin("com.android.library") || project.plugins.hasPlugin("com.android.application")) {
        project.android {
            signingConfigs {
                debug {
                    if (project.path.equals(":kotlin-app")) {
                        storeFile project.rootProject.file("config/signing/debug_2.keystore")
                    } else if (project.path.equals(":app")) {
                        storeFile project.file("debug.keystore")
                    } else {
                        storeFile project.rootProject.file("config/signing/debug.keystore")
                    }
                }
            }
            buildTypes {
                debug {
                    signingConfig signingConfigs.debug
                }
                release {
                    signingConfig signingConfigs.debug
                }
            }
        }
    }
    if (project.plugins.hasPlugin("com.android.application")) {
        variants = project.android.applicationVariants
    } else {
        variants = project.android.libraryVariants
    }

    if (project.plugins.hasPlugin("com.squareup.sqldelight")) {
        variants.all {

            project.android.sourceSets."${it.name}".java.srcDir project.file("build/generated/source/sqldelight")
            project.android.sourceSets."${it.name}".kotlin.srcDir project.file("build/generated/source/sqldelight")

            project.afterEvaluate { proj ->
                Task okbuckTask = proj.tasks.getByName("okbuck")
                Task sqlDelightTask = proj.tasks.getByName("generate${it.name.capitalize()}SqlDelightInterface")
                okbuckTask.dependsOn(sqlDelightTask)
            }
        }
    }
}

okbuck {
    buildToolVersion = config.build.buildTools
    target = "android-${config.build.compileSdk}"

    extraDepCachesMap << [tools:true]

    primaryDexPatterns = [
            "app": [
                    "^com/uber/okbuck/example/AppShell^",
                    "^com/uber/okbuck/example/BuildConfig^",
                    "^androidx/multidex/",
                    "^com/facebook/buck/android/support/exopackage/",
                    "^com/github/promeg/xlog_android/lib/XLogConfig^",
                    "^com/squareup/leakcanary/LeakCanary^",
                    "^com/uber/okbuck/example/common/Calc^",
                    "^com/uber/okbuck/example/common/BuildConfig^",
            ]
    ]
    exopackage = [
            "appDevDebug": true
    ]
    appLibDependencies = [
            "appProd": [
                    "buck-android-support",
                    "androidx.multidex:multidex",
                    "libraries/javalibrary:main",
                    "libraries/common:paidRelease",
            ],
            "appDev" : [
                    "buck-android-support",
                    "androidx.multidex:multidex",
                    "libraries/javalibrary:main",
                    "libraries/common:freeDebug",
            ],
            "appDemo": [
                    "buck-android-support",
                    "androidx.multidex:multidex",
                    "libraries/javalibrary:main",
                    "libraries/common:paidRelease",
            ]
    ]
    buckProjects = project.subprojects.findAll { it.name != "plugin" && it.name != "transform-cli" }

    lintExclude.put("another-app", ["debug"])

    legacyAnnotationProcessorSupport = false

    intellij {
        sources = true
    }

    test {
        espresso = true
        espressoForLibraries = true
        robolectric = true
        robolectricApis = ["21", "27"]
        enableIntegrationTests = true
    }

    wrapper {
        watch += ["**/*.sq"]
    }

    kotlin {
        version = deps.versions.kotlin
    }

    lint {
        version = deps.versions.androidTools
        jvmArgs = '-Xmx1g'
    }

    transform {
        transforms = [
                "appProd": [
                        [transform: "com.uber.okbuck.transform.DummyTransform"]
                ]

        ]
    }

    jetifier {
        aarOnly = true
        exclude = [
            "androidx.*"
        ]
        customConfigFile = "tooling/jetifier/custom.config"
    }

    externalDependencies {
        resolutionAction = "latest"
        allowAllVersions = [
                "org.robolectric:android-all",
        ]
        autoValueConfigurations = [
            "autoValueAnnotations",
            "autoValueGson",
            "autoValueParcel",
        ]
    }

    dependencies {
        transform project(":dummy-transform")
    }

    libraryBuildConfig = false

    extraBuckOpts = [
            "appDebug": [
                    "android_binary": [
                            "trim_resource_ids = True"
                    ]
            ]
    ]

    ruleOverrides {
        defaultImportLocation = "//tooling/buck-defs:project_targets.bzl"
        defaultRuleNamePrefix = "project_"
        override {
            nativeRuleName = "android_binary"
        }
        override {
            nativeRuleName = "prebuilt_jar"
        }
        override {
            nativeRuleName = "android_module"
        }
    }
}

def autoValueDeps = [deps.apt.autoValue, deps.apt.autoValueAnnotations]
def autoValueGsonDeps = autoValueDeps + [deps.apt.autoValueGson]
def autoValueParcelDeps = autoValueDeps + [deps.apt.autoValueParcel]

afterEvaluate {
    dependencies {
        toolsExtraDepCache deps.external.saxon

        autoValueAnnotations autoValueDeps
        autoValueGson autoValueGsonDeps
        autoValueParcel autoValueParcelDeps
    }
}
"""

        pprint.pprint(find_keyword_block(content=content))
        print(find_include_file(content))

    def test_start(self):
        """

        :return:
        """
        data_path = os.path.join(EXAMPLE_DATA_PATH, 'plugins', 'gradle')
        pprint.pprint(start(code_dir=data_path))

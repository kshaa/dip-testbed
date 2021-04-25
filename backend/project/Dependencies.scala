import sbt._
import Versions._

object Dependencies {
  lazy val slickPackage = "com.typesafe.slick" %% "slick" % slickVersion
  lazy val playPackage =
    "org.scalatestplus.play" %% "scalatestplus-play" % playVersion % "test"
  lazy val guicePackage = "com.typesafe.play" %% "play-guice" % guiceVersion
}

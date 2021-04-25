import sbt._
import sbt.Keys._

object Settings {
  lazy val scalaSettings = Seq(
    scalaVersion := Versions.scalaVersion,
  )

  lazy val metaSettings = Seq(
    organization := "lv.veinbahs.krisjanis",
  )
  
  lazy val scalacSettings = Seq(
    scalacOptions := Seq(
      "-feature",
      "-deprecation",
      "-Xfatal-warnings",
    )
  )
}
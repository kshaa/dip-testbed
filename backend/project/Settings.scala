import sbt.Keys._
import play.sbt.PlayImport.PlayKeys._

object Settings {
  lazy val scalaSettings = Seq(
    scalaVersion := Versions.scalaVersion,
  )

  lazy val playDevSettings = Seq(
    devSettings := Seq(
      "play.server.http.idleTimeout" -> "75s",
    ),
  )

  lazy val metaSettings = Seq(
    organization := "lv.veinbahs.krisjanis",
  )

  lazy val scalacSettings = Seq(
    scalacOptions := Seq(
      "-feature",
      "-deprecation",
      "-Xfatal-warnings",
      "-Ywarn-unused",
    ),
  )
}

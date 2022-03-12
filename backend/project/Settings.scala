import sbt.Keys._
import play.sbt.PlayImport.PlayKeys._
import scalafix.sbt.ScalafixPlugin.autoImport.scalafixSemanticdb

object Settings {
  lazy val scalaSettings = Seq(
    scalaVersion := Versions.scalaVersion,
    semanticdbEnabled := true,
    semanticdbVersion := scalafixSemanticdb.revision,
//    scapegoatVersion := Versions.scapegoat
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
      "-Ywarn-unused",
    ),
  )
}

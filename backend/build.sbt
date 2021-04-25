import Settings._
import Dependencies._

lazy val root = (project in file("."))
  .settings(scalaSettings: _*)
  .settings(metaSettings: _*)
  .settings(scalacSettings: _*)
  .aggregate(domain, web)

lazy val domain = (project in file("domain"))
  .settings(scalaSettings: _*)
  .settings(metaSettings: _*)
  .settings(scalacSettings: _*)
  .settings(
    name := "domain"
  )

lazy val protocol = (project in file("protocol"))
  .settings(scalaSettings: _*)
  .settings(metaSettings: _*)
  .settings(scalacSettings: _*)
  .settings(
    name := "protocol"
  )

lazy val web = (project in file("web"))
  .enablePlugins(PlayScala)
  .settings(scalaSettings: _*)
  .settings(metaSettings: _*)
  .settings(scalacSettings: _*)
  .settings(
    name := "web",
    libraryDependencies ++= Seq(
      playPackage,
      slickPackage,
      guice
    )
  )

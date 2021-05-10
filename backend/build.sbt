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
    name := "domain",
  )

lazy val protocol = (project in file("protocol"))
  .settings(scalaSettings: _*)
  .settings(metaSettings: _*)
  .settings(scalacSettings: _*)
  .settings(
    name := "protocol",
  )

lazy val database = (project in file("database"))
  .dependsOn(domain)
  .settings(scalaSettings: _*)
  .settings(metaSettings: _*)
  .settings(scalacSettings: _*)
  .settings(
    name := "database",
    libraryDependencies ++= Seq(
      playSlickPackage,
      slickPackage,
      guicePackage,
      catsPackage,
    ),
  )

lazy val web = (project in file("web"))
  .enablePlugins(PlayScala)
  .dependsOn(database)
  .settings(scalaSettings: _*)
  .settings(metaSettings: _*)
  .settings(scalacSettings: _*)
  .settings(
    name := "web",
    libraryDependencies ++= Seq(
      playPackage,
      playSlickPackage,
      postgresqlJdbcPackage,
      h2JdbcPackage,
      playSlickEvolutionsPackage,
      slickPackage,
      guicePackage,
      catsPackage,
    ),
  )

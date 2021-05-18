import Settings._
import Dependencies._

lazy val root = (project in file("."))
  .settings(scalaSettings: _*)
  .settings(metaSettings: _*)
  .settings(scalacSettings: _*)
  .aggregate(domain, protocol, database, web)

lazy val domain = (project in file("domain"))
  .settings(scalaSettings: _*)
  .settings(metaSettings: _*)
  .settings(scalacSettings: _*)
  .settings(
    name := "domain",
  )

lazy val protocol = (project in file("protocol"))
  .dependsOn(domain)
  .settings(scalaSettings: _*)
  .settings(metaSettings: _*)
  .settings(scalacSettings: _*)
  .settings(
    name := "protocol",
    libraryDependencies ++= Seq(
      circeCorePackage,
      circeGenericPackage,
      circeParserPackage,
      scalaTestPackage,
    ),
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
      playGuicePackage,
      catsEffectPackage,
      jdbc,
    ),
  )

lazy val web = (project in file("web"))
  .enablePlugins(PlayScala)
  .dependsOn(domain)
  .dependsOn(database)
  .dependsOn(protocol)
  .settings(scalaSettings: _*)
  .settings(metaSettings: _*)
  .settings(scalacSettings: _*)
  .settings(
    name := "web",
    libraryDependencies ++= Seq(
      playPackage,
      playSlickPackage,
      playGuicePackage,
      playJdbcPackage,
      playSlickEvolutionsPackage,
      postgresqlJdbcPackage,
      h2JdbcPackage,
      slickPackage,
      catsEffectPackage,
      catsEffectTestingPackage,
    ),
  )

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
    libraryDependencies ++= Seq(
      circeCorePackage,
      circeParserPackage,
    ),
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
      circeGenericExtrasPackage,
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
      circeCorePackage,
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
  .settings(playDevSettings: _*)
  .settings(metaSettings: _*)
  .settings(scalacSettings: _*)
  .settings(
    name := "web",
    libraryDependencies ++= Seq(
      akkaClusterToolsPackage,
      akkaTestkitPackage,
      playPackage,
      playAkkaClusterShardingPackage,
      playCircePackage,
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

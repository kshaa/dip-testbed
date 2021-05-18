import sbt._
import Versions._

object Dependencies {
  lazy val slickPackage = "com.typesafe.slick" %% "slick" % slickVersion
  lazy val playPackage =
    "org.scalatestplus.play" %% "scalatestplus-play" % playVersion % "test"
  lazy val playJdbcPackage =
    "com.typesafe.play" %% "play-jdbc" % playJdbcVersion
  lazy val playGuicePackage = "com.typesafe.play" %% "play-guice" % playGuiceVersion
  lazy val playSlickPackage = "com.typesafe.play" %% "play-slick" % playSlickVersion
  lazy val playSlickEvolutionsPackage =
    "com.typesafe.play" %% "play-slick-evolutions" % playSlickEvolutionsVersion
  lazy val postgresqlJdbcPackage =
    "org.postgresql" % "postgresql" % postgresqlJdbcVersion
  lazy val h2JdbcPackage = "com.h2database" % "h2" % h2JdbcVersion
  lazy val catsEffectPackage = "org.typelevel" %% "cats-effect" % catsEffectVersion
  lazy val catsEffectTestingPackage =
    "org.typelevel" %% "cats-effect-testing-scalatest" % catsEffectTestingVersion % "test"
  lazy val circeCorePackage = "io.circe" %% "circe-core" % circeCoreVersion
  lazy val circeGenericPackage = "io.circe" %% "circe-generic" % circeGenericVersion
  lazy val circeParserPackage = "io.circe" %% "circe-parser" % circeParserVersion
  lazy val scalaTestPackage = "org.scalatest" %% "scalatest" % scalaTestVersion % "test"

}

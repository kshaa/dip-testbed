import sbt._
import Versions._

object Dependencies {
  lazy val slickPackage = "com.typesafe.slick" %% "slick" % slickVersion
  lazy val playPackage =
    "org.scalatestplus.play" %% "scalatestplus-play" % playVersion % "test"
  lazy val playSlickPackage = "com.typesafe.play" %% "play-slick" % playVersion
  lazy val playSlickEvolutionsPackage =
    "com.typesafe.play" %% "play-slick-evolutions" % playVersion
  lazy val postgresqlJdbcPackage =
    "org.postgresql" % "postgresql" % postgresqlJdbcVersion
  lazy val h2JdbcPackage = "com.h2database" % "h2" % h2JdbcVersion
  lazy val guicePackage = "com.typesafe.play" %% "play-guice" % guiceVersion
  lazy val catsPackage = "org.typelevel" %% "cats-effect" % catsVersion
}

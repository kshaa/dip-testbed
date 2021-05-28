package iotfrisbee.web.ioControls

import scala.concurrent.Future
import scala.language.implicitConversions
import cats.data.EitherT
import cats.effect.IO
import cats.implicits._
import play.api.mvc.Results.NotFound
import play.api.mvc.{Result, Codec => PlayCodec}
import play.api.http.{ContentTypeOf, Writeable}
import play.api.http.ContentTypes.JSON
import play.api.mvc.Results.Status
import io.circe.{Json, Decoder => CirceDecoder, Encoder => CirceEncoder}
import iotfrisbee.protocol.WebResult
import iotfrisbee.protocol.WebResult._
import iotfrisbee.web.ioControls.PipelineTypes.PipelineStage

object PipelineOps {
  implicit class RichFunctorOption[A](r: IO[Option[A]]) {
    implicit def orRes(res: Result): PipelineStage[IO, A] =
      EitherT {
        r.map(o => Either.fromOption(o, res))
      }

    implicit def orNotFound: PipelineStage[IO, A] = orRes(NotFound("Not Found"))
  }

  implicit class RichFunctor[A](r: IO[A]) {
    implicit def piped: PipelineStage[IO, A] =
      EitherT {
        r.map(a => Either.right[Result, A](a))
      }
  }

  implicit class RichFutureAction[A](f: Future[A]) {
    implicit def asIO: IO[A] = IO.fromFuture(IO(f))
  }

  implicit val contentTypeOfCirceJson: ContentTypeOf[Json] =
    ContentTypeOf[io.circe.Json](Some(JSON))

  implicit def writeableOfCirceJson(implicit codec: PlayCodec): Writeable[Json] =
    Writeable(obj => codec.encode(obj.noSpaces))

  implicit class RichPipelineWebResult[A: CirceEncoder: CirceDecoder](webResult: WebResult[A]) {
    def withHttpStatus(statusCode: Int): Result = Status(statusCode)(webResult.toJsonString).as(JSON)
  }

  implicit class RichPipelineSuccess[A: CirceEncoder: CirceDecoder](success: Success[A]) {
    def withHttpStatus(statusCode: Int): Result = Status(statusCode)(success.toJsonString).as(JSON)
  }

  implicit class RichPipelineFailure[A: CirceEncoder: CirceDecoder](failure: Failure[A]) {
    def withHttpStatus(statusCode: Int): Result = Status(statusCode)(failure.toJsonString).as(JSON)
  }
}

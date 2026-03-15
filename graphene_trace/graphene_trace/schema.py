import graphene
import healthcare.schema


class Query(
    healthcare.schema.Query,
    graphene.ObjectType
):
    pass


class Mutation(
    healthcare.schema.Mutation,
    graphene.ObjectType
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
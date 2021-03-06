from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
# Error: errores
class UserSerializer(serializers.ModelSerializer):
    ''' Serializador para el objeto de usuarios '''
    class Meta:
        model = get_user_model()
        fields = ('email','password','name')

        extra_kwargs = {'password':{'write_only':True, 'min_length':5}}

    def create(self,validated_data):
        ''' crear nuevo usuario con clave encriptada y retornarno '''
        return get_user_model().objects.create_user(**validated_data)

    def update(self,instance,validated_data):
        ''' Actualiza al usuario, configura el pass correctamente y lo retorna '''
        #obtiene el pass lo utiliza y lo borra
        password = validated_data.pop('password',None)
        user = super().update(instance,validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user

class AuthTokenSerializer(serializers.Serializer):
    ''' Serializador para el objeto de autenticacion del usuario '''
    email = serializers.CharField()
    password = serializers.CharField(
        # Mostrar la contraseña con puntos
        style ={'input_type':'password'},
        trim_whitespace=False
    )

    def validate(self,attrs):
        ''' Validar y autenticar usuario '''
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request = self.context.get('request'),
            username = email,
            password = password,
        )
        if not user:
            msg =_('Unable to authenticate with provived credentials')
            raise serializers.ValidationError(msg, code='authorization')

        # Retornar atributos
        attrs['user'] = user
        return attrs
